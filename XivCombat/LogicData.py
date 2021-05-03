from FFxivPythonTrigger import api, Utils, SaintCoinach

# from Lumina.Excel.GeneratedSheets import Action
action_sheet = SaintCoinach.realm.game_data.get_sheet('Action')
# action_sheet = lumina.lumina.GetExcelSheet[Action]()

invincible_effects = {325, 394, 529, 656, 671, 775, 776, 895, 969, 981, 1570, 1697, 1829, }


class NoMeActorException(Exception):
    pass


class TargetIsSelfException(Exception):
    pass


class TargetNotExistsException(Exception):
    pass


class ActorDeadException(Exception):
    pass


def is_actor_status_can_damage(actor):
    for eid, _ in actor.effects.get_items():
        if eid in invincible_effects:
            return False
    return True


class LogicData(object):
    def __init__(self, config: dict, nSkill=None, nAbility=None):
        self.nAbility = nAbility
        self.nSkill = nSkill
        self.config = config
        self.me = api.XivMemory.actor_table.get_me()
        if self.me is None: raise NoMeActorException()
        if not self.me.currentHP: raise ActorDeadException()

        self.current = api.XivMemory.targets.current
        if self.current is not None and self.current.id == self.me.id:
            raise TargetIsSelfException()
        self.focus = api.XivMemory.targets.focus
        if self.focus is not None and self.focus.can_select and self.focus.effectiveDistanceX < 30:
            self.target = self.focus
        elif self.current is not None:
            self.target = self.current
        else:
            self.target = None

        enemies = Utils.query(api.XivMemory.combat_data.enemies.get_item(), key=lambda x: x.can_select)
        enemies = api.XivMemory.actor_table.get_actors_by_id(*[enemy.id for enemy in enemies])

        self.enemies = list(Utils.query(enemies, key=is_actor_status_can_damage))
        self.enemies.sort(key=lambda enemy: enemy.effectiveDistanceX)

        if self.target is None:
            if self.enemies and config.get('find'):
                self.target = self.enemies[0]
                api.XivMemory.targets.set_current(self.target)
            else:
                raise TargetNotExistsException()

        self.job = api.XivMemory.player_info.job
        self.combo_id = api.XivMemory.combat_data.combo_state.action_id
        self.combo_remain = api.XivMemory.combat_data.combo_state.remain
        self.gauge = api.XivMemory.player_info.gauge
        self.effects = self.me.effects.get_dict()
        self.gcd = api.XivMemory.combat_data.cool_down_group.gcd_group.remain
        self.is_violent = config.get('violent')

        self.skill_cd_cache = dict()

    def is_single(self, dis=None, limit=2):
        if self.config['single']: return True
        count = 0
        for enemy in self.enemies:
            if dis is not None and enemy.effectiveDistanceX > dis:
                break
            count += 1
            if count >= limit:
                return False
        return True

    def skill_cd(self, action_id: int):
        if action_id not in self.skill_cd_cache:
            row = action_sheet[action_id]
            if self.me.level < row['ClassJobLevel']:
                self.skill_cd_cache[action_id] = 9999
            else:
                self.skill_cd_cache[action_id] = api.XivMemory.combat_data.cool_down_group[row['CooldownGroup']].remain
        return self.skill_cd_cache[action_id]

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
