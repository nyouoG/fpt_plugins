from FFxivPythonTrigger.Utils import circle, rotated_rect
from ..Strategy import *
from .. import Define

"""
3624：伤残
3617：重斩
3623：吸收斩
3632：噬魂斩
7392：血溅
7391：寂灭（64）
7390：血乱（68）

3621：释放
3641：吸血深渊
3643：精雕怒斩
16468：刚魂
16466：暗黑波动
16467：暗黑锋
3625：嗜血

3639:腐秽大地
"""
"""
1972：血乱
"""


def count_enemy(data: LogicData, skill_type: int):
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    if skill_type == 1:
        aoe = circle(data.me.pos.x, data.me.pos.y, 5)  # 转圈圈
    else:
        aoe = rotated_rect(data.me.pos.x, data.me.pos.y, 1.5, 10, data.me.target_radian(data.target))  # 波动
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 7)


class DarkKnightLogic(Strategy):
    name = "dark_knight_logic"

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_skill:  # 队列技能
            return data.config.get_query_skill()
        cnt = count_enemy(data, 1)
        if data.target_distance > 3 and cnt < 2: return
        if (data.gauge.blood >= (50 if data[16472] > 15 else 80) and res_lv(data) and data[16472]) or 1972 in data.effects:
            return UseAbility(7391 if cnt > 2 and data.me.level >= 64 else 7392)
        if data.combo_id == 3617 and data.me.level >= 2:
            return UseAbility(3623)
        elif data.combo_id == 3623 and data.me.level >= 26:
            return UseAbility(3632)
        elif data.combo_id == 3621 and data.me.level >= 72:
            return UseAbility(16468)
        return UseAbility(3621 if cnt > 1 and data.me.level >= 6 else 3617)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability:
            return data.config.get_query_ability()
        if not res_lv(data) or data.target_distance > 3: return
        if not data[16472] and data.gauge.blood >= 50:
            return UseAbility(16472)
        if not data[3639]:
            return UseAbility(3639)
        if not data[3641]:
            return UseAbility(3641)
        if not data[3643]:
            return UseAbility(3643)
        if not data[7390] and (data[16472] > 10 or data.gauge.blood >= 50):
            return UseAbility(7390)
        if not data[16466] and (data.me.currentMP >= (6000 if data.me.level >= 70 else 3000) or data.gauge.darkArt):
            return UseAbility(16467 if data.me.level >= 40 and count_enemy(data, 2) < 2 else 16466)
        if not data[3625]:
            return UseAbility(3625)
