from .LogicData import LogicData

"""
3624：伤残
3617：重斩
3623：吸收斩
3632：噬魂斩
7392：血溅
7391：寂灭（64）
7390：血乱（68）

3621：释放
3641：吸血深渊
3643：精雕怒斩
16468：刚魂
16466：暗黑波动
16467：暗黑锋
3625：嗜血

3639:腐秽大地
"""
"""
1972：血乱
"""


def dark_knight_logic(data: LogicData):
    single = data.is_single(dis=5)
    if data.gcd >= 1:
        if data.nAbility:
            return data.nAbility
        if not data.is_violent: return
        if not data[16472] and data.gauge.blood >= 50: return 16472
        if not data[3641]: return 3641
        if not data[3643]: return 3643
        if not data[3639]: return 3639
        if not data[7390] and (data[16472] > 10 or data.gauge.blood >= 50): return 7390
        if not data[16466] and (data.me.currentMP >= (6000 if data.me.level >= 70 else 3000) or data.gauge.darkArt):
            return data.lv_skill(16467, (40, 16466)) if single else 16466
            # return 16466
        if not data[3625]: return 3625
    elif data.gcd < 0.2:
        if data.nSkill:
            return data.nSkill
        if data.target.effectiveDistanceX > (3 if single else 5) + 2:
            if 15 < data.target.effectiveDistanceX or data.combo_id: return
            return data.lv_skill(3624, (15, None))
        if (data.gauge.blood >= (50 if data[16472] > 15 else 80) and data.is_violent and data[16472]) or 1972 in data.effects:
            return 7392 if data.is_single(dis=5, limit=3) else data.lv_skill(7391, (64, 7392))
        if data.combo_id == 3617 and data.me.level >= 2:
            return 3623
        elif data.combo_id == 3623 and data.me.level >= 26:
            return 3632
        elif data.combo_id == 3621 and data.me.level >= 72:
            return 16468
        return 3617 if single else 3621


fight_strategies = {"DarkKnight": dark_knight_logic}
