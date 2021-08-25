from FFxivPythonTrigger.Utils import circle
from ..Strategy import *
from .. import Define

"""
28,钢铁信念,10

9,先锋剑,1
15,暴乱剑,4
3538,沥血剑,54
21,战女神之怒,26（3539,王权剑,60）
16460,赎罪剑,76

7381,全蚀斩,6
16457,日珥斩,40


23,厄运流转,50
29,深奥之灵,30
7383,安魂祈祷,68

7384,圣灵,64
16458,圣环,72
16459,悔罪,80

24,投盾,15
16461,调停,74
16,盾牌猛击,10

7382,干预,62
3542,盾阵,35
17,预警,38
3540,圣光幕帘,56
7385,武装戍卫,70
30,神圣领域,50
3541,深仁厚泽,58
27,保护,45

20,战逃反应,2
"""
"""
1902,忠义之剑,可以发动赎罪剑
725,沥血剑,体力逐渐减少,
1368,安魂祈祷
76,"战逃反应"
"""


def count_enemy(data: LogicData, skill_type: int):
    """
    :param skill_type: 0:普通 1:悔罪
    """
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    if skill_type == 0:
        aoe = circle(data.me.pos.x, data.me.pos.y, 5)
    else:
        aoe = circle(data.target.pos.x, data.target.pos.y, 5)
    cnt = sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))
    if not cnt: return 0
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    return cnt


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 7)


class PaladinLogic(Strategy):
    name = "paladin_logic"

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_skill:  # 队列技能
            return data.config.get_query_skill()
        cnt = count_enemy(data, 0)
        if data.me.level >= 40 and data.combo_id == 7381: return UseAbility(16457)
        if cnt > 1 and data.me.level >= 6:
            if 1368 in data.effects and data.me.level >= 72 and (not data.is_moving or data.me.lv >= 78):
                return UseAbility(16459)
            else:
                return UseAbility(7381)
        if data.target_distance > 3: return
        if 1902 in data.effects and (res_lv(data) or data.effects[1902].timer < 2.5 * data.effects[1902].param):
            return UseAbility(16460)
        if data.combo_id == 9 and data.me.level >= 4:
            return UseAbility(15)
        if data.combo_id == 15 and data.me.level >= 26:
            if data.me.level >= 54:
                t_effect = data.target.effects.get_dict(source=data.me.id)
                if (725 not in t_effect or t_effect[725].timer < 5) and data.time_to_kill_target >= 10:
                    return UseAbility(3538)
            if 1902 in data.effects:
                return UseAbility(16460)
            return UseAbility(21)
        if 1368 in data.effects and (not data.is_moving or data.me.level >= 78):
            return UseAbility(7384 if data.effects[1368].timer > 3 and data.me.currentMP >= 4000 else 16459)
        else:
            return UseAbility(9)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability:
            return data.config.get_query_ability()
        if data.target_distance > 3: return
        if res_lv(data):
            if not data[20] and 1368 not in data.effects: return UseAbility(20)
            if not data[7383] and 76 not in data.effects and data.me.currentMP / data.me.maxMP > 0.8 and data.combo_id not in {7381, 9, 15}:
                return UseAbility(7383)
            if not data[29]: return UseAbility(29)
            if not data[23]: return UseAbility(23)
