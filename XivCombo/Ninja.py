from FFxivPythonTrigger import api

"""
2240,双刃旋,1
2241,残影,2
2242,绝风,4
7541,内丹,8
2245,隐遁,10
7863,扫腿,10
7542,浴血,12
2247,飞刀,15
2248,夺取,15
2258,攻其不备,18
7549,牵制,22
2255,旋风刃,26
2257,影牙,30
2259,天之印,30
2260,忍术,30
2265,风魔手里剑,30
2272,通灵之术,30
18805,天之印,30
18873,风魔手里剑,30
18874,风魔手里剑,30
18875,风魔手里剑,30
7548,亲疏自行,32
2261,地之印,35
2266,火遁之术,35
2267,雷遁之术,35
18806,地之印,35
18876,火遁之术,35
18877,雷遁之术,35
2254,血雨飞花,38
2262,缩地,40
2263,人之印,45
2268,冰遁之术,45
2269,风遁之术,45
2270,土遁之术,45
2271,水遁之术,45
18807,人之印,45
18878,冰遁之术,45
18879,风遁之术,45
18880,土遁之术,45
18881,水遁之术,45
2264,生杀予夺,50
7546,真北,50
16488,八卦无刃杀,52
3563,强甲破点突,54
3566,梦幻三段,56
2246,断绝,60
7401,通灵之术·大虾蟆,62
7402,六道轮回,68
7403,天地人,70
16489,命水,72
16491,劫火灭却之术,76
16492,冰晶乱流之术,76
16493,分身之术,80
17413,双刃旋,80
17414,绝风,80
17415,旋风刃,80
17416,影牙,80
17417,强甲破点突,80
17418,飞刀,80
17419,血雨飞花,80
17420,八卦无刃杀,80
"""

"""
1955,"断绝预备","可以发动断绝"
496,"结印","结成手印准备发动忍术"
"""


def single(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 2242 and lv >= 26:
        return 2255
    if combo_id == 2240 and lv >= 4:
        return 2242
    return 2240


def single_armor_crush(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    if combo_id == 2242 and lv >= 26:
        if lv >= 54 and api.XivMemory.player_info.gauge.hutonMilliseconds:
            return 3563
        return 2255
    if combo_id == 2240 and lv >= 4:
        return 2242
    return 2240


def multi(me):
    return 16488 if api.XivMemory.combat_data.combo_state.action_id == 2254 and me.level >= 52 else 2254


def assassinate(me):
    return 2246 if 1955 in me.effects.get_dict() else 3566


combos = {
    2255: single,  # 旋风刃：单体连
    3563: single_armor_crush,  # 旋风刃：单体连
    16488: multi,  # 八卦无刃杀：群体连
    2246: assassinate,  # 断绝:三段-断绝
}
