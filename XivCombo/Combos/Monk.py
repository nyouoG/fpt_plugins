
"""
53,连击,1
54,正拳,4
56,崩拳,6
60,金刚体势,15
61,双掌打,18
62,破坏神冲,26
66,破碎拳,30
70,地烈劲,30
73,疾风体势,34
71,罗刹冲,35
63,红莲体势,40
65,真言,42
16473,四面脚,45
69,震脚,50
74,双龙脚,50
4262,演武,52
3546,斗气,54
3547,阴阳斗气斩,54
3545,苍气炮,56
3543,斗魂旋风脚,60
7394,金刚极意,64
7395,红莲极意,68
7396,义结金兰,70
16474,万象斗气圈,74
16475,无我,78
16476,六合星导脚,80
"""
"""
107,魔猿形,摆出魔猿身形
108,盗龙形,摆出盗龙身形
109,猛豹形,摆出猛豹身形
110,震脚,能够打出三种身形的所有招式
2513,无相身形,能够打出三种身形的所有招式，并触发对应的追加效果
1861,连击效果提高,下次发动连击的威力提高
101,双掌打,攻击所造成的伤害提高
246,破碎拳,体力逐渐减少
"""


def single_normal(me):
    effects = me.effects.get_dict()
    if 108 in effects and me.level >= 4:
        return 54
    if 109 in effects and me.level >= 6:
        return 56
    if me.level >= 50 and 1861 not in effects:
        return 74
    return 53


def single_special(me):
    effects = me.effects.get_dict()
    # if 110 in effects or 2513 in effects:
    #     return 61 if 101 not in effects else 66
    if 108 in effects and me.level >= 4:
        return 54 if me.level < 18 else 61
    if 109 in effects and me.level >= 6:
        return 56 if me.level < 30 else 66
    if me.level >= 50 and 1861 not in effects:
        return 74
    return 53


def multi(me):
    effects = me.effects.get_dict()
    if 110 in effects or 2513 in effects:
        return 16473 if 101 in effects and effects[101].timer < 4 else 70
    if 108 in effects and me.level >= 4:
        return 54 if me.level < 18 else 61 if me.level < 45 else 16473
    if 109 in effects and me.level >= 6:
        return 56 if me.level < 30 else 70
    return 62
combos = {
    'mnk_single_normal': (53, single_normal),  # 普通技能
    'mnk_single_special': (74, single_special),  # buff/dot技能
    'mnk_multi': (70, multi),  # aoe技能
}

