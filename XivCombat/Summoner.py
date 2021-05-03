from FFxivPythonTrigger import api
from .LogicData import LogicData
import time

"""
165,召唤,4
170,召唤II,15
180,召唤III,30

16509,灵攻I,10
16512,灵攻II,40
184,内力迸发,50

164,毒菌,2
168,瘴气,6
178,猛毒菌,26
7424,剧毒菌,66
7425,瘴暍,66

174,灾祸,30
3580,三重灾祸,56

16510,能量抽取,35
16508,能量吸收,18
181,溃烂爆发,18
3578,痛苦核爆,52

16511,迸裂,40

163,毁灭,1
172,毁坏,38
3579,毁荡,54


3581,龙神附体,58
3582,死星核爆,60
7423,以太契约,64
7427,龙神召唤,70
7429,龙神迸发,70


173,复生,12



16230,医术,4

"""
"""
179,毒菌
180,瘴气
189,猛毒菌
1214,剧毒菌
1215,瘴暍
1212,毁坏强化
1867,灵泉

"""
last_d2 = time.perf_counter()


def summoner_logic(data: LogicData):
    lv = data.me.level
    d1 = 1214 if lv >= 66 else 189 if lv >= 26 else 179
    d2 = 1215 if lv >= 66 else 180
    t_effects = data.target.effects.get_dict()
    need_dot1 = lv >= 2 and (d1 not in t_effects or t_effects[d1].timer < 3)
    need_dot2 = lv >= 6 and (d2 not in t_effects or t_effects[d2].timer < 3)
    d3 = (need_dot1 or need_dot2) and not data[3580]
    a4 = 0 if 1212 not in data.effects else data.effects[1212].param
    need_speed = data[16508] <= data.gauge.aetherflowStacks * 2.5 or min(data[16512], data[16509]) < (5 if data[3581] > 10 or data.gauge.bahamutReady else 30) or d3 or not data[3581]
    is_single = data.is_single(dis=30, limit=3)
    count_type = 2 if data.gauge.phoenixReady else 1 if data.gauge.ReturnSummon else 0

    if data.gcd > 1:
        if (data.gauge.stanceMilliseconds and count_type == 0) and data.gauge.stanceMilliseconds < data.gcd * 1000 + 500 and lv >= 60:
            return 3582
        if data.gauge.bahamutReady and  min(data[16512], data[16509]) > 20:
            return 7427
        if data.gauge.stanceMilliseconds and count_type and not data[7429]:
            return 7429
        if d3: return 3580
        if not data[3581]: return 3581
        if not data[16508] and not data.gauge.aetherflowStacks:
            return 16508 if is_single or lv < 35 else 16510
        if not (data[184] or data.gauge.ReturnSummon): return 184
        if data.gauge.aetherflowStacks:
            if is_single and d1 in t_effects and d2 in t_effects and not data[181]: return 181
            if not is_single and lv >= 52 and not data[3578]: return 3578
    elif data.gcd < 0.2:
        global last_d2
        if data[3580] > 5:
            if not api.XivMemory.movement.speed and need_dot2 and last_d2 + 3 < time.perf_counter():
                last_d2 = time.perf_counter()
                return 168
            if need_dot1: return 164
        if data.gauge.phoenixReady and data.gauge.stanceMilliseconds:
            return 16511 if 1867 in data.effects else 163
        if a4 >= 4: return 172
        if (api.XivMemory.movement.speed or need_speed) and not (data.gauge.stanceMilliseconds and count_type==0):
            if min(data[16512], data[16509]) < 30 and a4 < 4 and not data.gauge.ReturnSummon: return 16509 if data[16509] < data[16512] else 16512
            return 172
        else:
            return 163 if is_single or lv < 40 else 16511


fight_strategies = {27: summoner_logic}
