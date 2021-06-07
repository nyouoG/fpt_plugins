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
last_ea = time.perf_counter()


def summoner_logic(data: LogicData):
    global last_d2, last_ea
    is_single = data.is_single(dis=30, limit=3)
    lv = data.me.level
    t_effects = data.target.effects.get_dict(source=data.me.id)

    if data.gauge.phoenixReady:
        summon_type = 5 if data.gauge.stanceMilliseconds else 4  # 不死鸟附体ing/准备
    elif data.gauge.ReturnSummon:
        summon_type = 3  # 龙神召唤ing
    elif data.gauge.stanceMilliseconds:
        summon_type = 1  # 龙神附体
    elif data.gauge.bahamutReady:
        summon_type = 2  # 龙神召唤准备
    else:
        summon_type = 0  # 普通状态

    d1 = 1214 if lv >= 66 else 189 if lv >= 26 else 179
    d2 = 1215 if lv >= 66 else 180
    need_dot1 = lv >= 2 and (d1 not in t_effects or t_effects[d1].timer < 3) and data.time_to_kill_target > 20
    need_dot2 = lv >= 6 and (d2 not in t_effects or t_effects[d2].timer < 3) and data.time_to_kill_target > 20
    d3 = (need_dot1 or need_dot2 or not data[3581]) and not data[3580]  # 是否需要三灾 —— 任意一个dot需要补 or 附体冷却好

    enkindle_use = not (data[184] or data.gauge.ReturnSummon) and data.is_violent  # 宝宝大招 —— cd好了 and 不在不死鸟龙神召唤
    summon_enkindle_use = data.gauge.ReturnSummon and not data[7429]  # 是否可以使用迸发 —— 好了就用
    aether_use = data[16508] <= data.gauge.aetherflowStacks * 2.4  # 是否需要泄以太

    if data.gcd > 1.2:
        should_summon = last_ea < time.perf_counter()  # 判断上次灵攻时间，防止卡掉技能
        if data.nAbility:
            return data.nAbility
        if not data[7423] and data.is_violent:
            if summon_type == 1 and data.gauge.stanceMilliseconds < 6000 or enkindle_use or summon_type == 2 or summon_type == 4 and data[3581] < 6:
                last_ea = time.perf_counter() + 1
                return 7423  # 龙神附体末端 ， 召唤前,大招前 灵护好了就用
        if summon_type == 1 and data.gauge.stanceMilliseconds < data.gcd * 1000 + 500 and lv >= 60:
            return 3582  # 死星核爆 附体剩余时间少于 (剩余gcd+0.5s)
        if data.gauge.bahamutReady and min(data[16512], data[16509]) > 20 and data[184] > 20 and should_summon and data.is_violent and data.gcd < 2.2:
            return 7427 if data.gcd < 1.4 else None  # 召唤龙神 灵攻以及宝宝大招cd均在20s往上，判断上次灵攻时间
        if summon_enkindle_use: return 7429  # 迸发
        if d3:
            last_d2 = time.perf_counter()
            return 3580  # 三灾
        if not data[3581] and data.is_violent and (summon_type != 4 or should_summon) and data.gcd < 2.2:
            return 3581 if data.gcd < 1.5 else None  # 附体好了就用（前提泄三灾），判断上次灵攻时间
        if not data[16508] and not data.gauge.aetherflowStacks:
            return 16508 if is_single or lv < 35 else 16510  # 超流 没有以太存货就发动
        if enkindle_use:
            last_ea = time.perf_counter() + 1
            return 184  # 宝宝大招
        if data.gauge.aetherflowStacks and (data.is_violent or aether_use):  # 消耗以太相关
            if is_single or lv < 52:
                if not (need_dot1 or need_dot2) and not data[181]:
                    return 181
            elif not data[3578]:
                return 3578
        if data.me.currentMP < 7000 and not data[7562]:
            return 7562  # 醒梦

    elif data.gcd < 0.2:
        if data.nSkill:
            return data.nSkill
        if min(data[3580], data[3581]) > 5:  # 三灾cd中补毒相关
            if not api.XivMemory.movement.speed and need_dot2 and last_d2 + 3 < time.perf_counter():
                last_d2 = time.perf_counter()
                return 168  # 读条毒，需要防止对方buff未刷新而重复读
            if need_dot1:
                return 164  # 瞬发毒

        if summon_type == 5: return 16511 if 1867 in data.effects else 163  # 鸟状态打12121212

        r4 = 0 if 1212 not in data.effects else data.effects[1212].param  # r4层数
        if r4 >= 4: return 172  # 防止r4溢出

        ea_amount = 30 if summon_type == 2 or (summon_type == 4 and data[3581] < 8) else 5
        ea_use = not data.gauge.ReturnSummon and min(data[16512], data[16509]) <= ea_amount  # 是否需要泄灵攻
        bahamut_last_gcd = summon_type == 3 and data.gauge.stanceMilliseconds <= 5000  # 巴哈最后两个gcd打瞬发防止丢波

        need_speed = api.XivMemory.movement.speed or aether_use or ea_use or d3
        need_speed = need_speed or enkindle_use or summon_enkindle_use or bahamut_last_gcd or not data[3581]

        if need_speed and (summon_type != 1 or ea_use):  # 巴哈附体期间如果需要泄灵攻依然打灵攻
            if r4 < 4 and not data.gauge.ReturnSummon and min(data[16512], data[16509]) <= 30:
                last_ea = time.perf_counter() + 1
                return 16509 if data[16509] < data[16512] else 16512  # 有灵攻就用
            return 172  # r2摆烂咯（好吧应该有r4
        else:
            return 163 if is_single or lv < 40 else 16511  # r3还是aoe


fight_strategies = {'Summoner': summoner_logic}
