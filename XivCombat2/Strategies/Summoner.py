from time import perf_counter

from FFxivPythonTrigger.Utils import sector, circle

from ..Strategy import *
from .. import Define

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


def is_single(data: LogicData, skill_type: int) -> int:
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    aoe = circle(data.target.pos.x, data.target.pos.y, 5 if skill_type == 0 else 8)  # 0:迸裂,1:灾祸
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(1e+10 > data.max_ttk > 15)


class SummonerLogic(Strategy):
    name = "summoner_logic"

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)
        self.last_d2 = perf_counter()
        self.last_ea = perf_counter()

    def summoner_init(self, data: LogicData):
        lv = data.me.level
        t_effects = data.target.effects.get_dict(source=data.me.id)
        res = res_lv(data)

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

        enkindle_use = not (data[184] or data.gauge.ReturnSummon) and res  # 宝宝大招 —— cd好了 and 不在不死鸟龙神召唤
        summon_enkindle_use = data.gauge.ReturnSummon and not data[7429]  # 是否可以使用迸发 —— 好了就用
        aether_use = data[16508] <= data.gauge.aetherflowStacks * 2.4  # 是否需要泄以太

        swift_res_target = None
        k = data.config.custom_settings.setdefault('swift_res', 'none')
        if k == 'party':
            d = data.valid_party
        elif k == 'alliance':
            d = data.valid_alliance
        elif k == 'all':
            d = data.valid_players
        else:
            d = list()
        for member in d:
            if not member.currentHP and 148 not in member.effects.get_dict() and data.actor_distance_effective(member) < 30:
                swift_res_target = member
                break

        return res, summon_type, need_dot1, need_dot2, d3, enkindle_use, summon_enkindle_use, aether_use, swift_res_target

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_skill:  # 队列技能
            return data.config.get_query_skill()
        res, summon_type, need_dot1, need_dot2, d3, enkindle_use, summon_enkindle_use, aether_use, swift_res_target = self.summoner_init(data)

        if 167 in data.effects and swift_res_target is not None:
            return UseAbility(173, swift_res_target.id)

        if min(data[3580], data[3581]) > 5:  # 三灾cd中补毒相关
            if (not data.is_moving or 167 in data.effects) and need_dot2 and self.last_d2 + 3 < perf_counter():
                self.last_d2 = perf_counter()
                return UseAbility(168)  # 读条毒，需要防止对方buff未刷新而重复读
            if need_dot1:
                return UseAbility(164)  # 瞬发毒

        if summon_type == 5: return UseAbility(16511 if 1867 in data.effects else 163)  # 鸟状态打12121212

        r4 = 0 if 1212 not in data.effects else data.effects[1212].param  # r4层数
        if r4 >= 4: return UseAbility(172)  # 防止r4溢出

        ea_amount = 30 if summon_type == 2 or (summon_type == 4 and data[3581] < 8) else 5
        ea_use = not data.gauge.ReturnSummon and min(data[16512], data[16509]) <= ea_amount  # 是否需要泄灵攻
        bahamut_last_gcd = summon_type == 3 and data.gauge.stanceMilliseconds <= 5000  # 巴哈最后两个gcd打瞬发防止丢波

        need_speed = data.is_moving or aether_use or ea_use or d3
        need_speed = need_speed or enkindle_use or summon_enkindle_use or bahamut_last_gcd or (not data[3581] and res)
        need_speed = 167 not in data.effects and need_speed

        if need_speed and (summon_type != 1 or ea_use):  # 巴哈附体期间如果需要泄灵攻依然打灵攻
            if r4 < 4 and not data.gauge.ReturnSummon and min(data[16512], data[16509]) <= 30:
                self.last_ea = perf_counter() + 1
                return UseAbility(16509 if data[16509] < data[16512] else 16512)  # 有灵攻就用
            return UseAbility(172)  # r2摆烂咯（好吧应该有r4
        else:
            return UseAbility(163 if is_single(data, 0) or data.me.level < 40 else 16511)  # r3还是aoe

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability:
            return data.config.get_query_ability()
        res, summon_type, need_dot1, need_dot2, d3, enkindle_use, summon_enkindle_use, aether_use, swift_res_target = self.summoner_init(data)
        if swift_res_target is not None and not data[7561]:
            return UseAbility(7561)
        should_summon = self.last_ea < perf_counter()  # 判断上次灵攻时间，防止卡掉技能
        if not data[7423] and res:
            if summon_type == 1 and data.gauge.stanceMilliseconds < 6000 or enkindle_use or summon_type == 2 or summon_type == 4 and data[3581] < 6:
                self.last_ea = perf_counter() + 1
                return UseAbility(7423)  # 龙神附体末端 ， 召唤前,大招前 灵护好了就用
        if summon_type == 1 and data.gauge.stanceMilliseconds < data.gcd * 1000 + 500 and data.me.level >= 60:
            return UseAbility(3582)  # 死星核爆 附体剩余时间少于 (剩余gcd+0.5s)
        if data.gauge.bahamutReady and min(data[16512], data[16509]) > 20 and data[184] > 20 and should_summon and res and data.gcd < 2.2:
            if data.config.ability_cnt and data.gcd > 1:
                return None
            elif data.gcd <= 1:
                return UseAbility(7427)  # 召唤龙神 灵攻以及宝宝大招cd均在20s往上，判断上次灵攻时间
        if summon_enkindle_use:
            return UseAbility(7429)  # 龙、不死鸟迸发
        if d3 and self.last_d2 + 3 < perf_counter():
            self.last_d2 = perf_counter()
            return UseAbility(3580)  # 三灾
        if not data[3581] and res and (summon_type != 4 or should_summon) and data.gcd < 2.2:
            if data.config.ability_cnt and data.gcd > 1.3:
                return None
            elif data.gcd <= 1.3:
                return UseAbility(3581)  # 附体好了就用（前提泄三灾），判断上次灵攻时间
        if not data[16508] and not data.gauge.aetherflowStacks:
            return UseAbility(16508 if is_single(data, 0) < 3 or data.me.level < 35 else 16510)  # 超流 没有以太存货就发动
        if enkindle_use:
            self.last_ea = perf_counter() + 1
            return UseAbility(184)  # 宝宝大招
        if data.gauge.aetherflowStacks and (res or aether_use):  # 消耗以太相关
            if is_single(data, 0) < 3 or data.me.level < 52:
                if not (need_dot1 or need_dot2) and not data[181]:
                    return UseAbility(181)
            elif not data[3578]:
                return UseAbility(3578)
        if data.me.currentMP < 7000 and not data[7562]:
            return UseAbility(7562)  # 醒梦
