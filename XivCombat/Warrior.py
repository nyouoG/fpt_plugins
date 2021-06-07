from .LogicData import LogicData


def warrior_logic(data: LogicData):
    single = data.is_single(5)
    strid = data.lv_skill(7389, (70, 38))
    strbf = data.lv_skill(1177, (70, 86))
    use_strength = 1177 in data.effects or data.gauge.beast >= (70 if data.me.level > 70 and data[strid] > 5 else 50)
    red = (90 in data.effects and data.effects[90].timer > 7) or data.me.level < 50
    if data.gcd > 0.9:
        if data.nAbility:
            return data.nAbility
        if not data.is_violent: return
        if data[52] < 60 and data.gauge.beast <= 50 and (data[52] < data[strid] + 10 or strbf in data.effects):
            return 52
        if red:
            if not data[strid]:
                return strid
            if data.target.effectiveDistanceX < 4 and not data[7387]:
                return 7387
    elif data.gcd < 0.2:
        if data.nSkill:
            return data.nSkill
        if (red and use_strength) or data.gauge.beast == 100:
            return 49 if single else data.lv_skill(51, (45, 49))
        if single or not red:
            if data.target.effectiveDistanceX > 5:
                return 46
            if data.combo_id == 31:
                return data.lv_skill(37, (4, 31))
            elif data.combo_id == 37:
                return 45 if not red else data.lv_skill(42, (26, 31))
            else:
                return 31
        else:
            if data.target.effectiveDistanceX > 8:
                return 46
            elif data.combo_id == 41:
                return data.lv_skill(16462, (40, 41))
            else:
                return 41


fight_strategies = {'Warrior': warrior_logic}
