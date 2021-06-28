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
725,沥血剑,体力逐渐减少,
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
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


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
        if cnt > 2:
            if data.me.level >= 40 and data.combo_id == 7381: return UseAbility(16457)
            if data.me.level >= 6: return UseAbility(7381)
        if data.target_distance > 3: return
        if data.combo_id == 9 and data.me.level >= 4:
            return UseAbility(15)
        if data.combo_id == 15 and data.me.level >= 26:
            if data.me.level >= 54:
                t_effect = data.target.effects.get_dict(source=data.me.id)
                if 725 not in t_effect or t_effect[725].timer < 5:
                    return UseAbility(3538)
            return UseAbility(21)
        return UseAbility(9)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability:
            return data.config.get_query_ability()
        if data.target_distance > 3: return
        if res_lv(data):
            if not data[20]: return UseAbility(20)
            if not data[29]: return UseAbility(29)
            if not data[23]: return UseAbility(23)
