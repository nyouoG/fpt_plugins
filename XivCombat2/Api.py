from FFxivPythonTrigger import api
from FFxivPythonTrigger.AttrContainer import AttributeNotFoundException
from FFxivPythonTrigger.Utils import query


def get_me_actor():
    return api.XivMemory.actor_table.get_me()


def get_actor_by_id(a_id: int):
    return api.XivMemory.actor_table.get_actor_by_id(a_id)


def get_actors_by_id(*a_id: int):
    return api.XivMemory.actor_table.get_actors_by_id(*a_id)


def get_current_target():
    return api.XivMemory.targets.current


def get_focus_target():
    return api.XivMemory.targets.focus


def get_mo_target():
    try:
        return api.MoPlus.entity
    except AttributeNotFoundException:
        return api.XivMemory.targets.mouse_over


def set_current_target(actor):
    api.XivMemory.targets.set_current(actor)


def get_enemies_iter():
    return api.XivMemory.combat_data.enemies.get_item()


def get_current_job():
    return api.XivMemory.player_info.job.value()


def get_combo_state():
    return api.XivMemory.combat_data.combo_state


def get_gauge():
    return api.XivMemory.player_info.gauge


def get_gcd_group():
    return api.XivMemory.combat_data.cool_down_group.gcd_group


def get_actor_dps(a_id: int):
    return api.CombatMonitor.actor_dps(a_id)


def get_actor_tdps(a_id: int):
    return api.CombatMonitor.actor_tdps(a_id)


def get_cd_group(cd_group: int):
    return api.XivMemory.combat_data.cool_down_group[cd_group]


def reset_cd(cd_group: int):
    temp = get_cd_group(cd_group)
    temp.duration = temp.total


def use_action(action_id: int, target_id: int = 0xE0000000):
    api.XivMemory.combat_data.skill_queue.use_skill(action_id, target_id)


def use_area_action(action_id: int, x: float, y: float, z: float, target=0xE0000000):
    api.Magic.do_action.do_action_location(1, action_id, x, y, z, target)


def use_area_action_to_target(action_id: int, target_actor):
    use_area_action(action_id, target_actor.pos.x, target_actor.pos.y, target_actor.pos.z, target_actor.id)


def do_action(action_type: int, action_id: int, target: int):
    api.Magic.do_action.do_action(action_type, action_id, target)


def use_item(item_id: int, is_hq=False, target_id: int = 0xE0000000):
    api.Magic.do_action.use_item(item_id + 1000000 if is_hq else item_id, target_id)


def use_common(action_id: int, target_id: int = 0xE0000000):
    api.Magic.do_action.common_skill_id(action_id, target_id)


def get_ani_lock():
    return api.XivMemory.combat_data.skill_ani_lock


def reset_ani_lock():
    api.XivMemory.combat_data.skill_ani_lock = 0


def skill_queue_is_empty():
    return not api.XivMemory.combat_data.skill_queue.mark1


def get_backpack_item_count(item_id: int, is_hq: bool = None):
    cnt = 0
    for item in api.XivMemory.inventory.get_item_in_pages_by_key(item_id, "backpack"):
        if is_hq is None or item.is_hq == is_hq: cnt += item.count
    return cnt


def get_movement_speed():
    return api.XivMemory.movement.speed


def get_party_list(alliance_all=False):
    if alliance_all:
        return api.XivMemory.party.alliance()
    return api.XivMemory.party.main_party()


def get_players():
    return query(api.XivMemory.actor_table.get_item(), lambda actor: actor.type == 1)


def get_hostiles():
    return query(api.XivMemory.actor_table.get_item(), lambda actor: actor.can_select and actor.is_hostile)


def get_coordinate():
    return api.Coordinate()
