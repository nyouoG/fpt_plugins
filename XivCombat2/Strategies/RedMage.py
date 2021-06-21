from math import radians

from FFxivPythonTrigger.Logger import debug
from FFxivPythonTrigger.Utils import sector, circle
from ..Strategy import *
from .. import Define

"""
7503,摇荡,2
7504,回刺,1
7505,赤闪雷,4
7506,短兵相接,6
7507,赤疾风,10
7509,散碎,15
7510,赤火炎,26
7511,赤飞石,30
7512,交击斩,35
7513,划圆斩,52
7514,赤治疗,54
7515,移转,40
7516,连攻,50
7517,飞刺,45
7518,促进,50
7519,六分反击,56
7520,鼓励,58
7521,倍增,60
7523,赤复活,64
7524,震荡,62
7525,赤核爆,68
7526,赤神圣,70
7527,魔回刺,1
7528,魔交击斩,35
7529,魔连攻,50
7530,魔划圆斩,52
7559,沉稳咏唱,44
7560,昏乱,8
7561,即刻咏唱,18
7562,醒梦,24
"""
"""
1234,赤火炎预备
1235,赤飞石预备
167,即刻咏唱
1249,连续咏唱
"""
rdm_aoe_angle = radians(120)


def search_swift_res(data: LogicData):
    if data.me.level < 64: return
    k = data.config.custom_settings.setdefault('swift_res', 'none')
    if k == 'party':
        d = data.valid_party
    elif k == 'alliance':
        d = data.valid_alliance
    elif k == 'all':
        d = data.valid_players
    else:
        d = list()
    for member in d:
        if not member.currentHP and 148 not in member.effects.get_dict() and data.actor_distance_effective(member) < 30:
            return member


def count_enemy(data: LogicData, skill_type: int):
    """
    :param skill_type: 0:冲击疾风震雷    1:六分    2:画圆斩
    """
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    if skill_type == 0:
        aoe = circle(data.target.pos.x, data.target.pos.y, 5)  # 冲击疾风震雷
    elif skill_type == 1:
        aoe = circle(data.target.pos.x, data.target.pos.y, 6)  # 六分
    else:
        aoe = sector(data.me.pos.x, data.me.pos.y, 8, rdm_aoe_angle, data.me.target_radian(data.target))  # 画圆斩
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 6)


class RDMLogic(Strategy):
    name = "rdm_logic"
    fight_only = False

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_skill: return data.config.get_query_skill()  # 队列技能
        res = res_lv(data)
        lv = data.me.level
        dis = data.target_distance
        min_mana = min(data.gauge.white_mana, data.gauge.black_mana)
        max_mana = max(data.gauge.white_mana, data.gauge.black_mana)
        use_white = data.gauge.white_mana < data.gauge.black_mana
        has_swift = 1249 in data.effects or 167 in data.effects
        swift_res_target = search_swift_res(data)

        if data.target is None and swift_res_target is not None and data.me.currentMP >= (2400 if has_swift else 3100):
            if has_swift:
                return UseAbility(7523, swift_res_target.id)
            elif not data.is_moving:
                return UseAbility(7514, data.me.id)
            elif not data[7561]:
                return UseAbility(7561)

        if dis > 25 or not data.valid_enemies: return

        if data.me.level >= 52 and count_enemy(data, 2) > 2 and min_mana >= (90 if not res else 20 if data[7521] else 50):
            return UseAbility(7513)  # 人数够了就画圆

        "处理魔连击开始"
        if data.combo_id == 7504 and lv >= 35:
            return UseAbility(7512) if dis < 4 else None
        elif data.combo_id == 7512 and lv >= 50:
            return UseAbility(7516) if dis < 4 else None
        elif data.combo_id == 7529 and lv >= 68:
            if lv < 70: return UseAbility(7525)
            if data.gauge.white_mana == data.gauge.black_mana:
                if 1234 in data.effects: return UseAbility(7526)
                if 1235 in data.effects: return UseAbility(7525)
            return UseAbility(7526 if use_white else 7525)
        elif (data.combo_id == 7525 or data.combo_id == 7526) and lv >= 80:
            return UseAbility(16530)
        "处理魔连击结束"

        if min_mana >= 5:  # 续斩处理溢出魔元、走位
            if max_mana >= (90 if res else 97) and dis > 10: return UseAbility(16529)
            # if res and data.is_moving and not has_swift:
            #     if data.gcd:
            #         return None
            #     else:
            #         return UseAbility(16529)  # 续斩处理溢出魔元、走位

        if (lv < 2 or res and min_mana >= (80 if lv >= 50 else 55 if lv >= 35 else 30)) and dis < 4:
            return UseAbility(7516)  # 魔回刺、判断是否适合开始魔连击

        cnt = count_enemy(data, 0)
        if has_swift:  # 有瞬发
            if swift_res_target is not None and data.me.currentMP >= 2400:
                debug('swift_res',swift_res_target.Name, hex(swift_res_target.id))
                return UseAbility(7523, swift_res_target.id)
            if lv >= 15 and cnt > (1 if lv >= 66 else 2):
                return UseAbility(7509)  # aoe 散碎、冲击
            if lv >= 4:
                return UseAbility(7507 if use_white and lv >= 10 else 7505)  # 闪雷、疾风
        if not data.is_moving and lv >= 2:
            if cnt > 2 and lv >= 18:
                return UseAbility(16525 if use_white and lv >= 22 else 16524)
            if use_white:
                if 1234 in data.effects: return UseAbility(7510)
                if 1235 in data.effects: return UseAbility(7511)
            else:
                if 1235 in data.effects: return UseAbility(7511)
                if 1234 in data.effects: return UseAbility(7510)
            return UseAbility(7503)
        # else:
        #     return UseAbility(7561)  # 即刻

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability: return data.config.get_query_ability()  # 队列技能

        if data.target is None or not data.valid_enemies: return
        min_mana = min(data.gauge.white_mana, data.gauge.black_mana)
        if res_lv(data) and data.target_distance:
            if not data[7521] and 40 <= min_mana <= 50: return UseAbility(7521)  # 倍增
            if not data[7518] and min_mana < 60: return UseAbility(7518)  # 促进
            if not data[7520] and min_mana >= (50 if count_enemy(data, 2) < 3 else 20): return UseAbility(7520)  # 鼓励
            if not data[7517]: return UseAbility(7517)  # 飞刺
            if not data[7519]: return UseAbility(7519)  # 六分
        if not data[7562] and data.me.currentMP < 7000: return UseAbility(7562)  # 醒梦
