from .LogicData import LogicData

"""
15989：瀑泻（1）
15990：喷泉（2）
15991：逆瀑泻（20）
15992：坠喷泉（40）
15993：风车（15）
15994：落刃雨（25）
15995：升风车（35）
15996：落血雨（45）
16007：扇舞·序（30）
16008：扇舞·破（50）
16009：扇舞·急（66）
15997：标准舞步（15）
15998：技巧舞步（70）
16005：剑舞（76）
16011：直爆舞
16013：百花
"""
"""
1814,逆瀑泻预备
1815,坠喷泉预备
1816,升风车预备
1817,落血雨预备
1818,标准舞步
1819,技巧舞步
1820,扇舞·急预备
1821,标准舞步结束
1822,技巧舞步结束
"""


def step_to_skill(step):
    return 15998 + step.raw_value if step.raw_value > 0 else None


def dancer_common(data: LogicData):
    if 1818 in data.effects and data.gcd < 0.3 and data.gauge.currentStep < 2:
        return step_to_skill(data.gauge.step[data.gauge.currentStep])
    elif 1819 in data.effects and data.gcd < 0.3 and data.gauge.currentStep < 4:
        return step_to_skill(data.gauge.step[data.gauge.currentStep])


def dancer_logic(data: LogicData):
    if 1818 in data.effects:
        if data.gcd < 0.3:
            if data.gauge.currentStep < 2:
                return step_to_skill(data.gauge.step[data.gauge.currentStep])
            elif data.is_violent:
                return 15997
    elif 1819 in data.effects:
        if data.gcd < 0.3:
            if data.gauge.currentStep < 4:
                return step_to_skill(data.gauge.step[data.gauge.currentStep])
            elif data.is_violent:
                return 15998
    elif data.gcd > 1:
        if data.nAbility:
            return data.nAbility
        if data[15998] > 110 and not data[16011]:
            return 16011
        if data[15998] > 30 and not data[16013] and not {1815, 1814, 1817, 1816}.intersection(set(data.effects.keys())):
            return 16013
        if 1820 in data.effects:
            return 16009
        if data.gauge.feathers >= (1 if data.is_violent and 1822 in data.effects else 4):
            return 16007 if data.is_single(dis=5) else data.lv_skill(16008, (50, 16007))
    elif data.gcd < 0.3:
        if data.nSkill:
            return data.nSkill
        if data.is_single(dis=5):
            if 1821 not in data.effects and not data[15997]:
                return 15997
            if data.is_violent and not data[15998]:
                return 15998
            if data.gauge.esprit > 80 and data.is_violent:
                return 16005
            for e in {1815, 1814}:
                if e in data.effects and data.effects[e].timer < 3: return e + 14177
            for e in {1817, 1816}:
                if e in data.effects and data.effects[e].timer < 3: return e + 14179
            if not data[15997] and data[15998] > 5 and (data.is_violent or data.effects[1821].timer < 5):
                return 15997
            if data.is_violent and data.gauge.esprit >= 50 and 1822 in data.effects:
                return 16005
            for e in {1815, 1814}:
                if e in data.effects: return e + 14177
            if data.target.effectiveDistanceX <= 5:
                for e in {1817, 1816}:
                    if e in data.effects: return e + 14179
            if data.combo_id == 15989:
                return data.lv_skill(15990, (2, 15989))
            else:
                return 15989
        else:
            if (1821 not in data.effects or data.effects[1821].timer < 5) and not data[15997]:
                return 15997
            if data.gauge.esprit > 80 and data.is_violent:
                return 16005
            if data.is_violent and not data[15998]:
                return 15998
            for e in {1817, 1816}:
                if e in data.effects: return e + 14179
            if data.target.effectiveDistanceX <= 5:
                for e in {1815, 1814}:
                    if e in data.effects: return e + 14177
            if data.combo_id == 15993:
                return data.lv_skill(15994, (25, 15993))
            else:
                return 15993


fight_strategies = {"Dancer": dancer_logic}
common_strategies = {"Dancer":dancer_common}
