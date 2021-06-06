from FFxivPythonTrigger import api

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


def single(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 9 and lv >= 4:
        return 15
    if combo_id == 15 and lv >= 26:
        target = api.XivMemory.targets.current
        if lv >= 54 and target is not None:
            t_effect = target.effects.get_dict(source=me.id)
            if 725 not in t_effect or t_effect[725].timer < 5:
                return 3538
        return 21
    return 9


def multi(me):
    if me.level >= 40 and api.XivMemory.combat_data.combo_state.action_id == 7381:
        return 16457
    return 7381


combos = {
    16460: single,  # 赎罪剑：单体连
    16457: multi  # 日珥斩：群体连
}
