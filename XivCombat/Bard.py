from time import perf_counter

from .LogicData import LogicData

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


def archer_logic(data: LogicData):
    lv = data.me.level
    is_single = data.is_single(12)
    if data.gcd > 1:
        if data.nAbility:
            return data.nAbility
        if data.is_violent and not data[101]:
            return 101
        if not data[110]:
            return 110
    elif data.gcd < 0.3:
        if data.nSkill:
            return data.nSkill
        if 122 in data.effects:
            return 98
        poison, wind = (124, 129) if lv < 64 else (1200, 1201)
        t_effects = data.target.effects.get_dict()
        need_poison = (poison not in t_effects or t_effects[poison].timer < 2.5) and data.time_to_kill_target > 10
        need_wind = (wind not in t_effects or t_effects[wind].timer < 2.5) and data.time_to_kill_target > 10
        if need_poison:
            return 100
        if lv >= 30 and need_wind:
            return 113
        # if lv > 56 and (need_wind or need_poison) and poison in t_effects and wind in t_effects:
        #     return 3560
        return 106 if not is_single and lv >= 18 else 97


LAST_SONG = perf_counter()
ability_cnt = 0


def bard_dots(data: LogicData):
    lv = data.me.level
    song = data.gauge.songType.value()
    poison, wind = (124, 129) if lv < 64 else (1200, 1201)
    t = data.gcd_total * 2 if 125 not in data.effects or data.effects[125].timer > 7 else 15
    t_effects = data.target.effects.get_dict(source=data.me.id)
    need_poison = (poison not in t_effects or t_effects[poison].timer < t) and data.time_to_kill_target > 10
    need_wind = (wind not in t_effects or t_effects[wind].timer < t) and data.time_to_kill_target > 10
    if lv > 56 and (need_wind or need_poison) and poison in t_effects and wind in t_effects: return 3560
    if need_poison: return 100
    if lv >= 30 and need_wind: return 113
    if not song: return
    cnt = 1
    if song == "paeon":
        cnt_cut = 2
    elif song == 'ballad' or song == 'minuet':
        cnt_cut = 4
    else:
        return
    for e in data.enemies:
        if e.id == data.target.id or e.effectiveDistanceX > 24: continue
        t_effects = e.effects.get_dict(source=data.me.id)
        need_wind = (wind not in t_effects or t_effects[wind].timer < t)
        need_poison = (poison not in t_effects or t_effects[poison].timer < t)
        if not (need_wind and need_poison): cnt += 1
        if cnt > cnt_cut:
            return
        need_wind = need_wind and data.get_ttk(e.id) > 10
        need_poison = need_poison and data.get_ttk(e.id) > 20
        if lv > 56 and (need_wind or need_poison) and poison in t_effects and wind in t_effects:
            return 3560, e.id
        if need_poison:
            return 100, e.id
        if lv >= 30 and need_wind:
            return 113, e.id


def get_ability(data: LogicData):
    lv = data.me.level
    is_single = data.is_single(12)
    song = data.gauge.songType.value()
    if data.is_violent:
        global LAST_SONG
        poison, wind = (124, 129) if lv < 64 else (1200, 1201)
        t_effects = data.target.effects.get_dict(source=data.me.id)
        need_poison = (poison not in t_effects or t_effects[poison].timer < data.gcd_total) and data.time_to_kill_target > 10
        need_wind = (wind not in t_effects or t_effects[wind].timer < data.gcd_total) and data.time_to_kill_target > 10
        full_dot = not (need_poison or need_wind)
        if not data[101] and full_dot:
            if ability_cnt and data.gcd > 1.5:
                return
            elif data.gcd <= 1.5:
                return 101
        if not data[118] and data[101] > 10 and song: return 118
        if not data[107] and full_dot and 122 not in data.effects and 125 in data.effects: return 107
        if not data[3562] and full_dot: return 16494 if not is_single and lv >= 72 else 3562
        song_end = not song or data.gauge.songMilliseconds < data.gcd
        is_p = song == "paeon" and data.gauge.songProcs > 3 and max([data[3559], data[114]]) <= 30
        if perf_counter() - LAST_SONG > 3:
            if is_single:
                if not data[3559] and (song_end or is_p):
                    LAST_SONG = perf_counter()
                    return 3559
                if not data[114] and (song_end or is_p):
                    LAST_SONG = perf_counter()
                    return 114
            else:
                if not data[114] and (song_end or is_p):
                    LAST_SONG = perf_counter()
                    return 114
                if not data[3559] and (song_end or is_p):
                    LAST_SONG = perf_counter()
                    return 3559
            if not data[116] and song_end:
                LAST_SONG = perf_counter()
                return 116
    if song == "minuet" and data.gauge.songProcs > (2 if data.gauge.songMilliseconds > data.gcd_total * 1000 else 0): return 7404
    if not data[110]: return 117 if not is_single and lv >= 45 else 110
    if not data[3558] and (lv < 68 or song): return 3558


def get_skill(data: LogicData):
    lv = data.me.level
    is_single = data.is_single(12)
    if data.nSkill: return data.nSkill
    if 122 in data.effects: return 98
    use_dot = bard_dots(data)
    if type(use_dot) != int and data.gauge.soulGauge >= 90: return 16496
    if use_dot is not None: return use_dot
    return 106 if not is_single and lv >= 18 else 97


def bard_logic(data: LogicData):
    global ability_cnt
    if data.target.effectiveDistanceX > 24: return
    if data.gcd > 0.7 and ability_cnt < int(data.gcd_total):
        rtn = get_ability(data) if not data.nAbility else data.nAbility
        if rtn is not None:
            ability_cnt += 1
            return rtn
    elif data.gcd < 0.2:
        rtn = get_skill(data) if not data.nSkill else data.nSkill
        if rtn is not None:
            ability_cnt = 0
            return rtn


fight_strategies = {
    "Bard": bard_logic,
    "Archer": archer_logic
}
