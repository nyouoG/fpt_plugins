from FFxivPythonTrigger import api
from FFxivPythonTrigger.Logger import Logger
def get_combo_state():
    return api.XivMemory.combat_data.is_in_fight
#剩余几秒替换 默认3 请根据技速自己改嗷
r=3
#学者
SCHdots=[179,189,1895]
'''
                    buffid
17864,毒菌,2        179
17865,猛毒菌,26     189
16540,蛊毒法,72     1895
17869,毁灭,1
3584,气炎法,54
7435,魔炎法,64
16541,死炎法,72
'''
#占星
'''
3599,烧灼,4         838
3608,炽灼,46        843
16554,焚灼,72       1881
3596,凶星
'''
ASTdots=[838,843,1881]
#白魔
'''
121,疾风,4          143
132,烈风,46         144
16532,天辉,72       1871
119,飞石,1
124,医治,10
133,医济,50         150
'''
WHMdots=[143,144,1871]


def SCHdot(me):
    if not get_combo_state():
        return 17869
    else:
        target = api.XivMemory.targets.current
        if target is None: return 17864
        t_effects = target.effects.get_dict(source=me.id)
        dot=set(SCHdots) & set(t_effects)
        if dot == set([]):return 17864
        return 17864 if t_effects[list(dot)[0]].timer < r else 17869
def ASTdot(me):
    if not get_combo_state():
        return 3596
    else:
        target = api.XivMemory.targets.current
        if target is None: return 3599
        t_effects = target.effects.get_dict(source=me.id)
        dot=set(ASTdots) & set(t_effects)
        if dot == set([]):return 3599
        return 3599 if t_effects[list(dot)[0]].timer < r else 3596
def WHMdot(me):
    if not get_combo_state():
        return 119
    else:
        target = api.XivMemory.targets.current
        if target is None: return 121
        t_effects = target.effects.get_dict(source=me.id)
        dot=set(WHMdots) & set(t_effects)
        if dot == set([]):return 121
        return 121 if t_effects[list(dot)[0]].timer < r else 119
def Medica(me):
        lv = me.level
        effects = me.effects.get_dict(source=me.id)
        if lv > 50:
            if 150 in effects:
                if effects[150].timer > 5:
                    return 124
            return 133
        else:
            return 124

combos = {
    'sch_dot': (17869, SCHdot), #毁灭->智能dot 有毒上毒没毒打1
    'ast_dot': (3596, ASTdot),  #凶星
    'whm_dot': (119, WHMdot),   #飞石
    'MedicaII': (133,Medica)    #医济
}