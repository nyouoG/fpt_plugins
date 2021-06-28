from FFxivPythonTrigger import api

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
"""


def single(me):
    effects = me.effects.get_dict()
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    gauge = api.XivMemory.player_info.gauge
    bm = effects[1298].timer if 1298 in effects else 0
    bf = effects[1299].timer if 1299 in effects else 0
    if 1233 in effects:
        if not bf: return 7479
        if not bm: return 7478
        if not gauge.flower: return 7482
        if not gauge.moon: return 7481
        if not gauge.snow: return 7480
        return 7482
    if combo_id == 7478 and me.level >= 30:
        return 7481
    if combo_id == 7479 and me.level >= 40:
        return 7482
    if combo_id == 7477:
        if me.level >= 50 and bm > 10 and bf > 10 and not gauge.snow:
            return 7480
        if me.level >= 18 and (bf < 7 or me.level >= 40 and not gauge.flower and bf < bm):
            return 7479
        if me.level >= 4:
            return 7479 if me.level >= 18 and bf < bm and (me.level < 30 or gauge.moon) else 7478
    return 7477


def multi(me):
    effects = me.effects.get_dict()
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    gauge = api.XivMemory.player_info.gauge
    bm = effects[1298].timer if 1298 in effects else 0
    bf = effects[1299].timer if 1299 in effects else 0
    if combo_id == 7483 and me.level >= 35 or 1233 in effects:
        if me.level < 45: return 7484
        if not gauge.flower: return 7485
        if not gauge.moon: return 7484
        if not bf: return 7485
        return 7484 if bf > bm else 7485
    return 7483


def kaeshi(me):
    return 16483 if me.level >= 76 and api.XivMemory.player_info.gauge.prev_kaeshi_lv else 7867


combos = {
    7477: single,  # 刃风，单体
    7483: multi,  # 风雅，群体
    7867: kaeshi,  # 居合，燕回返
}
