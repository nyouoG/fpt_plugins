import math
from functools import lru_cache

from FFxivPythonTrigger.Utils import circle, sector, rotated_rect
from ..Strategy import *
from .. import Define

"""
7477,刃风,1
7478,阵风,4
7479,士风,18
7480,雪风,50
7481,月光,30
7482,花车,40
7483,风雅,26
7484,满月,35
7485,樱花,45
7486,燕飞,15
7490,必杀剑·震天,62
7491,必杀剑·九天,64
7492,必杀剑·晓天,54
7493,必杀剑·夜天,56
7494,必杀剑·回天,52
7495,叶隐,68
7496,必杀剑·红莲,70
7497,默想,60
7498,心眼,6
7499,明镜止水,50
7501,必杀剑·星眼,66
7502,慈眼,58
7867,居合术,30
16481,必杀剑·闪影,72
16482,意气冲天,68
16483,燕回返,76
16484,回返彼岸花,76
16485,回返五剑,76
16486,回返雪月花,76
16487,照破,80
"""
"""
1299,士风
1298,阵风
1233,明镜止水
1252,开眼
1236,燕飞效果提高
1228,彼岸花
1229,必杀剑·回天
"""

sam_sector_angle = math.radians(120)


@lru_cache
def count_enemy(data: LogicData, skill_type: int):
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    if skill_type == 1:
        aoe = circle(data.me.pos.x, data.me.pos.y, 5)  # 转圈圈
    elif skill_type == 2:
        aoe = sector(data.me.pos.x, data.me.pos.y, 8, sam_sector_angle, data.me.target_radian(data.target))  # 五剑阵风
    else:
        aoe = rotated_rect(data.me.pos.x, data.me.pos.y, 2, 10, data.me.target_radian(data.target))  # 红莲
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 7)


def cal_kenki_v1(data: LogicData):
    if data.me.level < 52: return 0
    will_add = 0 if data[16482] else 50
    sen = sum([data.gauge.flower, data.gauge.moon, data.gauge.snow])
    if sen: return data.gauge.kenki - 30 + will_add
    will_add += 20
    if will_add:
        if data.combo_id == 7477 or data.combo_id == 7483: will_add -= 5
        if data.combo_id == 7478 or data.combo_id == 7479: will_add -= 10
    return min(data.gauge.kenki + will_add - 30, data.gauge.kenki)


def cal_kenki_v2(data: LogicData):
    if data.me.level < 52: return 0
    will_add = 0 if data[16482] else 50
    sen = sum([data.gauge.flower, data.gauge.moon, data.gauge.snow])
    if sen > 1: return data.gauge.kenki - 30 + will_add
    will_add += 30 - sen * 15
    if will_add:
        if data.combo_id == 7477 or data.combo_id == 7483: will_add -= 5
        if data.combo_id == 7478 or data.combo_id == 7479: will_add -= 10
    return min(data.gauge.kenki + will_add - 30, data.gauge.kenki)


def cal_kenki_v3(data: LogicData):
    if data.me.level < 52: return 0
    will_add = 0 if data[16482] else 50
    if not data.gauge.moon: will_add += 15
    if not data.gauge.flower: will_add += 15
    if not data.gauge.snow: will_add += 20
    if will_add:
        if data.combo_id == 7477 or data.combo_id == 7483: will_add -= 5
        if data.combo_id == 7478 or data.combo_id == 7479: will_add -= 10
    return min(data.gauge.kenki + will_add - 30, data.gauge.kenki)


def choose_kaeshi(data: LogicData):
    if count_enemy(data, 2) > 2:
        return 2
    bm = data.effects[1298].timer if 1298 in data.effects else 0
    bf = data.effects[1299].timer if 1299 in data.effects else 0
    t_effects = data.target.effects.get_dict()
    if 1228 not in t_effects or t_effects[1228].timer < 7 and data.time_to_kill_target > 20 and min(bf, bm) > 20:
        return 1
    return 3


class SamuraiLogic(Strategy):
    name = "samuari_logic"

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)
        self.gcd_total = 2.5

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.gcd_total: self.gcd_total = data.gcd_total
        if data.config.query_skill:  # 队列技能
            return data.config.get_query_skill()
        bm = data.effects[1298].timer if 1298 in data.effects else 0
        bf = data.effects[1299].timer if 1299 in data.effects else 0
        sen = sum([data.gauge.flower, data.gauge.moon, data.gauge.snow])
        kaeshi = choose_kaeshi(data)
        res = res_lv(data)
        if bm and (sen == kaeshi or sen == 3):  # 居合
            if not data[16487] and data.gauge.meditation > 2 and res:
                return UseAbility(16487)
            if data.me.level < 52 or 1229 in data.effects:
                return None if data.is_moving else UseAbility(7867)
            elif data.me.level >= 52 and data.gauge.kenki >= 20:
                return UseAbility(7494)
        if not data[16483] and data.gauge.prev_kaeshi_lv > 1 and res_lv(data):  # 回返
            if not data[16487] and data.gauge.meditation > 2 and res:
                return UseAbility(16487)
            return UseAbility(16483)
        cnt1 = count_enemy(data, 1)
        cnt2 = count_enemy(data, 2)
        if 1233 in data.effects:
            if not bf: return UseAbility(7479)
            if not bm: return UseAbility(7478)
            if not data.gauge.snow and cnt2 < 3 and max(bf, bm) < 25:
                return UseAbility(7480)
            if not data.gauge.flower and not data.gauge.moon:
                return UseAbility((7482 if cnt1 < 3 else 7485) if bf >= bm else (7481 if cnt1 < 3 else 7484))
            if not data.gauge.flower: return UseAbility(7482 if cnt1 < 3 else 7485)
            if not data.gauge.moon: return UseAbility(7481 if cnt1 < 3 else 7484)
            if not data.gauge.snow and cnt2 < 3: return UseAbility(7480)
            return UseAbility((7482 if cnt1 < 3 else 7485) if bf >= bm else (7481 if cnt1 < 3 else 7484))
        if data.combo_id == 7478 and data.me.level >= 30:
            return UseAbility(7481)
        if data.combo_id == 7479 and data.me.level >= 40:
            return UseAbility(7482)
        if data.combo_id == 7477:
            if data.me.level >= 50 and bm > 8 and bf > 8 and not data.gauge.snow:
                return UseAbility(7480)
            if data.me.level >= 18 and (bf < self.gcd_total or data.me.level >= 40 and not data.gauge.flower and bf < bm):
                return UseAbility(7479)
            if data.me.level >= 4:
                return UseAbility(7479 if data.me.level >= 18 and bf < bm and (data.me.level < 30 or data.gauge.moon) else 7478)
        if data.combo_id == 7483 and data.me.level >= 35:
            if data.me.level < 45: return UseAbility(7484)
            if not data.gauge.flower: return UseAbility(7485)
            if not data.gauge.moon: return UseAbility(7484)
            return UseAbility(7484 if bf > bm else 7485)
        if data.me.level >= 15 and (1236 in data.effects or data.target_distance > 6):
            return UseAbility(7486)
        return UseAbility(7483 if bm and bf and cnt2 > 2 and data.me.level >= 26 else 7477)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.gcd_total: self.gcd_total = data.gcd_total
        if data.config.query_ability:
            return data.config.get_query_ability()
        if not res_lv(data): return

        if not data[16482] and data.gauge.kenki < 50:
            return UseAbility(16482)

        if 1298 not in data.effects:
            if data.gauge.kenki >= 90:
                cnt = count_enemy(data, 1)
                if 1252 in data.effects and data.me.level >= 66 and cnt < 3:
                    if not data[7501]: return UseAbility(7501)
                else:
                    if not data[7490]: return UseAbility(7491 if cnt > 2 and data.me.level >= 64 else 7490)
            return

        kaeshi = choose_kaeshi(data)

        sen = sum([data.gauge.flower, data.gauge.moon, data.gauge.snow])

        # 回天
        if not data[7494] and 1229 not in data.effects and data.gauge.kenki >= 20 and not data.is_moving:
            if sen == kaeshi or sen == 3: return UseAbility(7494)

        # 明镜
        if not data[7499] and 1299 in data.effects and not (sen == kaeshi or sen == 3):
            return UseAbility(7499)

        if kaeshi == 1:
            can_use = cal_kenki_v1(data)
        elif kaeshi == 2:
            can_use = cal_kenki_v2(data)
        else:
            can_use = cal_kenki_v3(data)
        if can_use < 1: return

        if not data[16481] and can_use >= 50:
            return UseAbility(7496 if count_enemy(data, 3) > 1 and data.me.level >= 70 else 16481)
        cnt = count_enemy(data, 1)
        if 1252 in data.effects and data.me.level >= 66 and cnt < 3:
            if not data[7501] and can_use >= (25 if data[16481] > 20 or data[16482] < 3 else 75):
                return UseAbility(7501)
        else:
            if not data[7490] and can_use >= (35 if data[16481] > 20 or data[16482] < 3 else 85):
                return UseAbility(7491 if cnt > 2 and data.me.level >= 64 else 7490)

        if not data[16487] and data.gauge.meditation > 2:
            return UseAbility(16487)
