from FFxivPythonTrigger import api


def single(me):
    lv = me.level
    combo_id = api.XivMemory.combat_data.combo_state.action_id
    red = me.effects.get_dict().get(90)
    if combo_id == 31 and lv >= 4:
        return 37
    elif combo_id == 37 and lv >= 26:
        if lv >= 50 and (red is None or red.timer < 30):
            return 45
        return 42
    return 31


def multi(me):
    if api.XivMemory.combat_data.combo_state.action_id == 41 and me.level >= 40:
        return 16462
    return 41


combos = {
    'war_single': (42, single),  # 暴风斩
    'war_multi': (16462, multi),  # 秘银暴风
}
