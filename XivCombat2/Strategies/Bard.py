from math import radians
from time import perf_counter

from FFxivPythonTrigger.Utils import sector, circle
from ..Strategy import *
from .. import Define

"""
3559,放浪神的小步舞曲,52
114,贤者的叙事谣,30
116,军神的赞美歌,40

3561,光阴神的礼赞凯歌,35
7408,大地神的抒情恋歌,66
7405,行吟,62

110,失血箭,12
117,死亡箭雨,45

101,猛者强击,4
107,纷乱箭,38
118,战斗之声,50

100,毒咬箭,6
113,风蚀箭,30
7406,烈毒咬箭,64
7407,狂风蚀箭,64
3560,伶牙俐齿,56

97,强力射击,1
98,直线射击,2
16495,爆发射击,76
7409,辉煌箭,70

106,连珠箭,18

3558,九天连箭,54
7404,完美音调,52
3562,侧风诱导箭,60
16494,影噬箭,72
16496,绝峰箭,80
"""
"""
125,猛者强击
122,直线射击预备
129,风蚀箭
1201,狂风蚀箭
124,毒咬箭
1200,烈毒咬箭

"""

bard_aoe_angle = radians(90)


def is_single(data: LogicData, skill_type: int) -> bool:
    if data.config.single == Define.FORCE_SINGLE: return True
    if data.config.single == Define.FORCE_MULTI: return False
    if skill_type == 0:
        aoe = sector(data.me.pos.x, data.me.pos.y, 12, bard_aoe_angle, data.me.target_radian(data.target))  # 连珠箭
    elif skill_type == 1:
        aoe = circle(data.me.pos.x, data.me.pos.y, 5)  # 影噬箭
    elif skill_type == 2:
        aoe = circle(data.me.pos.x, data.me.pos.y, 8)  # 死亡箭雨
    else:
        aoe = circle(data.me.pos.x, data.me.pos.y, 25)  # 死亡箭雨
    cnt = 0
    for enemy in data.valid_enemies:
        if aoe.intersects(enemy.hitbox):
            cnt += 1
            if cnt > 1: return False
    return True


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 7)


def bard_dots(data: LogicData):
    lv = data.me.level
    song = data.gauge.songType.value()
    poison, wind = (124, 129) if lv < 64 else (1200, 1201)
    t = data.gcd_total * 2 if 125 not in data.effects or data.effects[125].timer > 7 else 15
    t_effects = data.target.effects.get_dict(source=data.me.id)
    need_poison = (poison not in t_effects or t_effects[poison].timer < t) and data.time_to_kill_target > 10
    need_wind = (wind not in t_effects or t_effects[wind].timer < t) and data.time_to_kill_target > 10
    if lv > 56 and (need_wind or need_poison) and poison in t_effects and wind in t_effects: return 3560,
    if need_poison: return 100,
    if lv >= 30 and need_wind: return 113,
    if not song or data.config.single == Define.FORCE_SINGLE: return
    cnt = 1
    if song == "paeon":
        cnt_cut = 2
    elif song == 'ballad' or song == 'minuet':
        cnt_cut = 4
    else:
        return
    for e in data.valid_enemies:
        if e.id == data.target.id or data.actor_distance_effective(e) > 24: continue
        t_effects = e.effects.get_dict(source=data.me.id)
        need_wind = (wind not in t_effects or t_effects[wind].timer < t)
        need_poison = (poison not in t_effects or t_effects[poison].timer < t)
        if not (need_wind and need_poison): cnt += 1
        if cnt > cnt_cut:
            return
        need_wind = need_wind and data.ttk(e.id) > 10
        need_poison = need_poison and data.ttk(e.id) > 30
        if lv > 56 and (need_wind or need_poison) and poison in t_effects and wind in t_effects:
            return 3560, e.id
        if need_poison:
            return 100, e.id
        if lv >= 30 and need_wind:
            return 113, e.id


def song_logic(data: LogicData) -> Optional[int]:
    song = data.gauge.songType.value()
    song_end = not song or data.gauge.songMilliseconds / 1000 <= (data.gcd_total + data.gcd if song == 'paeon' else data.gcd)

    song_strategy = data.config.custom_settings.setdefault('song_strategy', '80')
    if data.me.level < 30:
        return
    elif data.me.level < 40:
        if not data[114]: return 114
    elif data.me.level < 52:
        if not data[116] and data[114] < 29 and song_end: return 116
        if not data[114] and song_end: return 114
    else:
        is_p = song_strategy == '80' and song == "paeon" and data.gauge.songProcs > 3 and max([data[3559], data[114]]) <= 30
        if is_single(data, 3):
            if not data[3559] and (song_end or is_p): return 3559
            if not data[114] and (song_end or is_p): return 114
        else:
            if not data[114] and (song_end or is_p): return 114
            if not data[3559] and (song_end or is_p): return 3559
        if not data[116] and song_end: return 116


class BardLogic(Strategy):
    name = "bard_logic"

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)
        self.last_song = perf_counter()

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_skill:
            return data.config.get_query_skill()
        lv = data.me.level
        if 122 in data.effects: return UseAbility(98)
        use_dot = bard_dots(data)
        if (use_dot is None or len(use_dot) < 2) and data.gauge.soulGauge >= 90: return UseAbility(16496)
        if use_dot is not None:
            return UseAbility(*use_dot)
        return UseAbility(106 if not is_single(data, 0) and lv >= 18 else 97)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability:
            return data.config.get_query_ability()
        lv = data.me.level
        song = data.gauge.songType.value()
        if res_lv(data):
            poison, wind = (124, 129) if lv < 64 else (1200, 1201)
            t_effects = data.target.effects.get_dict(source=data.me.id)
            need_poison = (poison not in t_effects or t_effects[poison].timer < data.gcd_total) and data.time_to_kill_target > 10
            need_wind = (wind not in t_effects or t_effects[wind].timer < data.gcd_total) and data.time_to_kill_target > 10
            full_dot = not (need_poison or need_wind)
            if not data[101] and full_dot:
                if data.config.ability_cnt and data.gcd > 1.5:
                    return
                elif data.gcd <=  1.5:
                    return UseAbility(101)
            if not data[118] and data[101] > 10 and song: return UseAbility(118)
            if not data[107] and full_dot and 122 not in data.effects and 125 in data.effects: return UseAbility(107)
            if not data[3562] and full_dot: return UseAbility(16494 if not is_single(data, 1) and lv >= 72 else 3562)

            if perf_counter() - self.last_song > 3:
                song_to_use = song_logic(data)
                if song_to_use is not None:
                    self.last_song = perf_counter()
                    return UseAbility(song_to_use)

        if song == "minuet" and data.gauge.songProcs > (2 if data.gauge.songMilliseconds > data.gcd_total * 1000 else 0): return UseAbility(7404)
        if not data[110]: return UseAbility(117 if not is_single(data, 2) and lv >= 45 else 110)
        if not data[3558] and (lv < 68 or song): return UseAbility(3558)
