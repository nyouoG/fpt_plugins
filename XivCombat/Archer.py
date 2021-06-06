from .LogicData import LogicData

"""
110,失血箭,12

101,猛者强击,4
107,纷乱箭,38

100,毒咬箭,6
113,风蚀箭,30

97,强力射击,1
98,直线射击,2

106,连珠箭,18

"""
"""
122,直线射击预备
129,风蚀箭
124,毒咬箭
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
        return 106 if not is_single and lv >=18 else 97


fight_strategies = {5: archer_logic}
