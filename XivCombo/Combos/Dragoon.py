from FFxivPythonTrigger import api

"""
7541,内丹,8
7863,扫腿,10
7542,浴血,12
7549,牵制,22
7548,亲疏自行,32
7546,真北,50

75,精准刺,1
78,贯通刺,4
83,龙剑,6
90,贯穿尖,15
87,开膛枪,18
84,直刺,26
85,猛枪,30
92,跳跃,30
94,回避跳跃,35
86,死天枪,40
95,破碎冲,45
88,樱花怒放,50
96,龙炎冲,50
3557,战斗连祷,52
3553,苍天龙血,54
3554,龙牙龙爪,56
3556,龙尾大回旋,58
3555,武神枪,60
7397,音速刺,62
7398,巨龙视线,66
7399,幻象冲,68
7400,死者之岸,70
16477,山境酷刑,72
16478,高跳,74
16479,龙眼雷电,76
16480,坠星冲,80
"""
"""
802,龙牙龙爪效果提高,可以发动龙牙龙爪
803,龙尾大回旋效果提高,可以发动龙尾大回旋
1243,幻象冲预备,可以发动幻象冲
1914,开膛枪,攻击所造成的伤害提高
"""


def single_normal(me):
    me_effect = me.effects.get_dict()
    if 802 in me_effect: return 3554
    if 803 in me_effect: return 3556
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 75 and lv >= 4: return 78
    if combo_id == 78 and lv >= 26: return 84
    return 75


def single_dot(me):
    me_effect = me.effects.get_dict()
    if 802 in me_effect: return 3554
    if 803 in me_effect: return 3556
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 75 and lv >= 18: return 87
    if combo_id == 87 and lv >= 50: return 88
    return 75


def multi(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 7397 and lv >= 72: return 16477
    if combo_id == 86 and lv >= 62: return 7397
    return 86


def jump(me):
    if 1243 in me.effects.get_dict(): return 7399
    return 92


combos = {
    'drg_single_normal': (84, single_normal),  # 直刺连
    'drg_single_dot': (88, single_dot),  # 樱花连
    'drg_multi': (16477, multi),  # 群体连
    'drg_jump': (7399, jump),  # 高跳、幻象冲
}
