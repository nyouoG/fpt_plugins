from .LogicData import LogicData

"""
16143：闪雷弹（15）
16137：利刃斩（1）
16139：残暴弹（4）
16145：迅连斩（26）
16141：恶魔切（10）
16149：恶魔杀（40）
16162：爆发击（30）
16163：命运之环（72）
16153：音速破（54）
16146：烈牙（60）
16147：猛兽爪（60）
16150：凶禽爪（60）
16155：续剑（70）
16144：危险领域（18/80)
16159：弓形冲波(62)
16138：无情(2)
16164：血壤（76）
"""
"""
1842：撕喉预备
1843：裂膛预备
1844：穿目预备
1831：无情
"""


def gunbreaker_logic(data: LogicData):
    single = data.is_single(dis=5)
    cartridges_full = data.combo_id in [16139, 16141 if data.me.level >= 40 else -1] and data.gauge.cartridges == 2
    s_dis = (4 if single else 5)
    has_spec = 1842 in data.effects or 1843 in data.effects or 1844 in data.effects
    if data.gcd > 1:
        if data.nAbility: return data.nAbility
        if data.target.effectiveDistanceX > s_dis: return
        if has_spec:
            return 16155
        if not data.is_violent: return
        if data.gcd < 2 and not data[16138] and (data[16164] < 10 or data[16164] > 25) and \
                data.combo_id in [16139, 16141 if data.me.level >= 40 else -1] and max(data[16159], data[16146],
                                                                                       data[16153] < 4) and data.gauge.cartridges:
            return 16138
        if not data[16164] and data[16138] > 10 and data.combo_id != 16139 and not data.gauge.cartridges:
            return 16164
        if not data[16144] and (data[16138] > 10 or 1831 in data.effects):
            return 16144
        if not data[16159] and 1831 in data.effects:
            return 16159
    elif data.gcd < 0.2:
        if data.nSkill: return data.nSkill
        if data.target.effectiveDistanceX > s_dis:
            if data.combo_id in [16139, 16137, 16141] or 15 < data.target.effectiveDistanceX or \
                    data.target.effectiveDistanceX < s_dis + 2 or data.gauge.continuationState or has_spec:
                return
            else:
                return data.lv_skill(16143, (15, None))
        if data.is_violent and not data[16146] and (data[16138] > 5 or 1831 in data.effects) and data.gauge.cartridges and data.is_single(dis=5,limit=4):
            return 16146
        if not data[16153] and 1831 in data.effects:
            return 16153
        if has_spec:
            return 16155
        if data.gauge.continuationState == 1:
            return 16147
        if data.gauge.continuationState == 2:
            return 16150
        if not single and data.combo_id == 16141 and data.gauge.cartridges < 2:
            return data.lv_skill(16149, (40, 16141))
        if single and data.combo_id == 16139 and data.gauge.cartridges < 2:
            return data.lv_skill(16145, (26, 16137))
        if cartridges_full or ((1831 in data.effects or data[16164] < 3 and data[16138] > 10) and data.gauge.cartridges):
            return 16162 if single else data.lv_skill(16163, (72, 16162))
        if single or data.me.level < 10:
            if data.combo_id == 16139:
                return data.lv_skill(16145, (26, 16137))
            if data.combo_id == 16137:
                return data.lv_skill(16139, (4, 16137))
            return 16137
        else:
            if data.combo_id == 16141:
                return data.lv_skill(16149, (40, 16141))
            else:
                return 16141


fight_strategies = {"Gunbreaker": gunbreaker_logic}
