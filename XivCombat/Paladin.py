from .LogicData import LogicData

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


def paladin_logic(data: LogicData):
    if data.target.effectiveDistanceX > 14: return
    is_single = data.is_single(dis=5)
    if data.gcd > 0.9:
        if data.nAbility:
            return data.nAbility
        if data.is_violent:
            if not data[20]:return 20
            if not data[29]:return 29
            if not data[23]:return 23
    elif data.gcd < 0.2:
        if data.target.effectiveDistanceX > 5:
            return 24 if not data.combo_id and data.me.level >= 15 else None
        if data.nSkill:
            return data.nSkill
        if not is_single:
            if data.me.level >= 40 and data.combo_id == 7381:
                return 16457
            if data.me.level >= 6:
                return 7381
        if data.target.effectiveDistanceX > 3:
            return
        if data.combo_id == 9 and data.me.level >= 4:
            return 15
        if data.combo_id == 15 and data.me.level >= 26:
            if data.me.level >= 54:
                t_effect = data.target.effects.get_dict(source=data.me.id)
                if 725 not in t_effect or t_effect[725].timer < 5:
                    return 3538
            return 21
        return 9

fight_strategies = {
    'Paladin': paladin_logic
}
