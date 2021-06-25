from functools import cached_property, lru_cache
from math import sqrt
from typing import TYPE_CHECKING

from FFxivPythonTrigger import Utils, SaintCoinach

from . import Api, Define

if TYPE_CHECKING:
    from . import Config

action_sheet = SaintCoinach.realm.game_data.get_sheet('Action')

invincible_effects = {325, 394, 529, 656, 671, 775, 776, 895, 969, 981, 1570, 1697, 1829, }
invincible_actor = set()


def is_actor_status_can_damage(actor):
    if actor.id in invincible_actor or not actor.can_select:
        return False
    for eid, _ in actor.effects.get_items():
        if eid in invincible_effects:
            return False
    return True


class LogicData(object):
    def __init__(self, config: 'Config.CombatConfig'):
        self.config = config

    @cached_property
    def me(self):
        return Api.get_me_actor()

    @cached_property
    def job(self):
        return Api.get_current_job()

    @cached_property
    def target(self):
        for method in self.config.target:
            t = self.get_target(method)
            if t is not None and is_actor_status_can_damage(t): return t

    @lru_cache
    def get_target(self, method: str):
        if method == "current":
            return self.current_target
        if method == "focus":
            return self.focus_target
        if method == "list_distance":
            return self.list_dis_target
        if method == "list_hp":
            return self.list_hp_target
        if method == "list_hpp":
            return self.list_hpp_target

    @cached_property
    def current_target(self):
        return Api.get_current_target()

    @cached_property
    def focus_target(self):
        return Api.get_focus_target()

    @cached_property
    def list_dis_target(self):
        if not self.valid_enemies: return
        return self.valid_enemies[0]

    @cached_property
    def list_hp_target(self):
        if not self.valid_enemies: return
        return min(self.valid_enemies, key=lambda x: x.currentHP)

    @cached_property
    def list_hpp_target(self):
        if not self.valid_enemies: return
        return min(self.valid_enemies, key=lambda x: x.currentHP / x.maxHp)

    @cached_property
    def valid_party(self):
        return [member.actor for member in Api.get_party_list() if member.actor is not None and member.actor.can_select]

    @cached_property
    def valid_alliance(self):
        return [member.actor for member in Api.get_party_list(alliance_all=True) if member.actor is not None and member.actor.can_select]

    @cached_property
    def valid_players(self):
        return [player for player in Api.get_players() if player.can_select]

    @cached_property
    def valid_enemies(self):
        enemies = Api.get_actors_by_id(*{enemy.id for enemy in Utils.query(Api.get_enemies_iter(), key=lambda x: x.can_select)})
        enemies = [enemy for enemy in enemies if is_actor_status_can_damage(enemy)]
        if self.config.enable_extra_enemies:
            enemy_id = {enemy.id for enemy in Api.get_enemies_iter()}
            extra_enemies = list()
            for enemy in Api.get_hostiles():
                if enemy.id not in enemy_id and self.valid_extra_enemies(enemy):
                    extra_enemies.append(enemy)
            enemies += extra_enemies
        return sorted(enemies, key=lambda enemy: enemy.effectiveDistanceX)

    @lru_cache
    def valid_extra_enemies(self, enemy):
        if enemy.effectiveDistanceY > self.config.extra_enemies_distance: return False
        if abs(enemy.pos.z - self.me.pos.z) > 5: return False
        if enemy.currentHP < 2: return False
        if self.config.extra_enemies_combat_only and not enemy.is_in_combat: return False
        return True

    @lru_cache
    def dps(self, actor_id):
        return Api.get_actor_dps(actor_id)

    @lru_cache
    def tdps(self, actor_id):
        return Api.get_actor_tdps(actor_id)

    @lru_cache
    def ttk(self, actor_id):
        t = Api.get_actor_by_id(actor_id)
        if t is None:
            return -1
        else:
            return t.currentHP / max(self.tdps(actor_id), 1)

    @cached_property
    def combo_state(self):
        return Api.get_combo_state()

    @property
    def combo_id(self):
        return self.combo_state.action_id

    @property
    def combo_remain(self):
        return self.combo_state.remain

    @cached_property
    def effects(self):
        return self.me.effects.get_dict()

    @cached_property
    def gauge(self):
        return Api.get_gauge()

    @cached_property
    def gcd_group(self):
        return Api.get_gcd_group()

    @property
    def gcd(self):
        return self.gcd_group.remain

    @property
    def gcd_total(self):
        return self.gcd_group.total

    @property
    def time_to_kill_target(self):
        if self.target is None: return 1e+99
        return self.ttk(self.target.id)

    @cached_property
    def max_ttk(self):
        if not len(self.valid_enemies): return 1e+99
        return max(self.ttk(e.id) for e in self.valid_enemies)

    def reset_cd(self, action_id: int):
        Api.reset_cd(action_sheet[action_id]['CooldownGroup'])

    def skill_cd(self, action_id: int):
        row = action_sheet[action_id]
        if self.me.level < row['ClassJobLevel'] or action_id in self.config.skill_disable:
            return 1e+99
        else:
            return Api.get_cd_group(row['CooldownGroup']).remain

    def lv_skill(self, base_id, *statements):
        me_lv = self.me.level
        for statement in statements:
            if me_lv >= statement[0]:
                break
            else:
                base_id = statement[1]
        return base_id

    def __getitem__(self, item):
        return self.skill_cd(item)

    @lru_cache
    def item_count(self, item_id, is_hq: bool = None):
        return Api.get_backpack_item_count(item_id, is_hq)

    @cached_property
    def is_moving(self):
        return bool(Api.get_movement_speed())

    @lru_cache
    def actor_distance_effective(self, target_actor):
        t_pos = target_actor.pos
        m_pos = self.coordinate
        return sqrt((t_pos.x - m_pos.x) ** 2 + (t_pos.y - m_pos.y) ** 2) - self.me.HitboxRadius - target_actor.HitboxRadius

    @cached_property
    def target_distance(self):
        t = self.target
        if t is None: return 1e+99
        return self.actor_distance_effective(t)

    @cached_property
    def coordinate(self):
        return Api.get_coordinate()
