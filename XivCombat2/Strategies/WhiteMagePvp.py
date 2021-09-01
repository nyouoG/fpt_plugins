from time import perf_counter

from FFxivPythonTrigger.Logger import info
from FFxivPythonTrigger.Utils import circle
from ..Strategy import *
from .. import Api

"""
天辉 2035 受到攻击的伤害增加
"""

TANK = 0
HEALER = 1
MELEE = 2
MAGICIAN = 3
SHOOTER = 4

DIS5 = 0
DIS10 = 1
DIS15 = 2
DIS25 = 3

job_function = {
    19: TANK,  # 骑士PLD
    20: TANK,  # 武僧MNK
    21: TANK,  # 战士WAR
    22: MELEE,  # 龙骑士DRG
    23: SHOOTER,  # 吟游诗人BRD
    24: HEALER,  # 白魔法师WHM
    25: MAGICIAN,  # 黑魔法师BLM
    27: MAGICIAN,  # 召唤师SMN
    28: HEALER,  # 学者SCH
    30: MELEE,  # 忍者NIN
    31: SHOOTER,  # 机工士MCH
    32: TANK,  # 暗黑骑士DRK
    33: HEALER,  # 占星术士AST
    34: MELEE,  # 武士SAM
    35: MAGICIAN,  # 赤魔法师RDM
    37: TANK,  # 绝枪战士GNB
    38: SHOOTER  # 舞者DNC
}

jobs_danger = [
    [
        # 5距离内, (10内目标, 10内目标身边), (15内目标, 15内目标身边), (25内目标, 25内目标身边)
        10, (10, 0), (1, 0), (1, 0)
    ],  # TANK
    [
        5, (5, 2), (5, 2), (5, 2)
    ],  # HEALER
    [
        15, (15, 10), (10, 5), (0, 0)
    ],  # MELEE
    [
        10, (10, 7), (10, 7), (10, 7)
    ],  # MAGICIAN
    [
        12, (12, 5), (12, 5), (12, 5)
    ],  # SHOOTER
]


class Member(object):
    around: list['Member']

    def __init__(self, data: LogicData, actor, is_party, select_alliance):
        self.is_party = is_party
        self.is_target = is_party or select_alliance
        self.actor = actor
        self.function = job_function.get(actor.job.raw_value, 5)
        self.dangers = {}
        self.danger = 0
        self.dis = data.actor_distance_effective(actor)
        self.hp_lv = (actor.currentHP / actor.maxHP - 0.001) // 0.15
        self.around = []

    def set_enemy_danger(self, enemy_id, danger):
        self.dangers[enemy_id] = max(self.dangers.setdefault(enemy_id, 0), danger)

    def cal_around(self, members):
        self.around = [member for member in members.values() if
                       self.actor.id != member.actor.id and self.actor.absolute_distance_xy(member.actor) <= 5]

    def cal_dangers(self, enemies):
        for enemy in enemies:
            ejob = enemy.job.raw_value
            if ejob in job_function:
                dis = self.actor.absolute_distance_xy(enemy)
                if dis < 5:
                    self.set_enemy_danger(enemy.id, jobs_danger[job_function[ejob]][DIS5])
                elif enemy.pcTargetId2 == self.actor.id:
                    if dis <= 10:
                        d_m, d_a = jobs_danger[job_function[ejob]][DIS10]
                    elif dis <= 15:
                        d_m, d_a = jobs_danger[job_function[ejob]][DIS15]
                    elif dis <= 25:
                        d_m, d_a = jobs_danger[job_function[ejob]][DIS25]
                    else:
                        continue
                    if d_m:
                        self.set_enemy_danger(enemy.id, d_m)
                    if d_a:
                        for member in self.around:
                            member.set_enemy_danger(enemy.id, d_m)

    def sum_dangers(self):
        self.danger = (sum(self.dangers.values()) // 5) / 2


class Enemy(object):
    def __init__(self, enemy, data: LogicData):
        self.enemy = enemy
        self.effects = enemy.effects.get_dict()
        self.hitbox = circle(enemy.pos.x, enemy.pos.y, 0.1)
        self.dis = data.actor_distance_effective(enemy)
        self.total_aoe = 0
        self.total_aoe_thunder = 0
        self.total_aoe_non_thunder = 0

    def cal_aoe_targets(self, enemies: list['Enemy'], area=5):
        aoe_area = circle(self.enemy.pos.x, self.enemy.pos.y, area)
        for enemy in enemies:
            if aoe_area.intersects(enemy.hitbox):
                self.total_aoe_non_thunder += 1
        self.total_aoe = self.total_aoe_thunder + self.total_aoe_non_thunder


def single(data: LogicData):
    if data.gcd < 0.3 and data.gauge.lilyStacks:
        return 17791
    elif data[13975] < 15:
        return 13975


def dot_key(enemy):
    return (enemy.effects[2035].timer if 2035 in enemy.effects else 0), -enemy.enemy.currentHP


class WhiteMagePvpLogic(Strategy):
    name = "white_mage_pvp_logic"
    fight_only = False

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)
        self.shield = 0
        self.last_t = 0

    def process_ability_use(self, data: LogicData, action_id: int, target_id: int) -> Optional[Tuple[int, int]]:
        t = Api.get_mo_target()
        if t: return action_id, t.id

    def common(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.me.currentHP / data.me.maxHP <= 0.7 and data[18943] <= 30:
            data.me.currentHP += 4000
            return UseAbility(18943, data.me.id)
        if data.gcd < 0.3 and data.gauge.lilyStacks or data[13975] < 15:
            party_ids = {member.id for member in data.valid_party}
            select_alliance = data.config.custom_settings.setdefault('whm_pvp_party_only', 'true') == 'false'
            enemies = [enemy for enemy in data.valid_enemies if enemy.id < 0x20000000]
            members = {member.id: Member(data, member, member.id in party_ids, select_alliance) for member in data.valid_alliance
                       if member.currentHP > 0 and data.target_action_check(8896, member)}
            if members:
                for member in members.values():
                    member.cal_around(members)
                for member in members.values():
                    member.cal_dangers(enemies)
                for member in members.values():
                    member.sum_dangers()
                members_need_healing = [member for m_id, member in members.items() if member.is_target and member.hp_lv < 5]
                if self.shield < perf_counter() - 30:
                    target = max([member for m_id, member in members.items() if member.is_target], key=lambda x: x.danger)
                    if target.danger > 5:
                        self.shield = perf_counter()
                        return UseAbility(17832, target.actor.id)
                if members_need_healing:
                    single_target = min(members_need_healing, key=lambda member: ((member.hp_lv - member.danger) // 2, member.function))
                    if single_target.hp_lv < 3 or single_target.hp_lv - single_target.danger < 1:
                        s = single(data)
                        if s:
                            single_target.actor.currentHP += 4000
                            return UseAbility(s, single_target.actor.id)
                    if data.gauge.lilyStacks:
                        members_heal_aoe = [member for member in members_need_healing if member.dis < 15 and member.is_party]
                        if len(members_heal_aoe) > (1 if data.gauge.lilyStacks > 2 else 2):
                            for member in members_heal_aoe: member.actor.currentHP += 2000
                            return UseAbility(18946, data.me.id)
                    if single_target.hp_lv < 4 or single_target.hp_lv - single_target.danger < 3 or data.gauge.lilyStacks > 2:
                        s = single(data)
                        if s:
                            single_target.actor.currentHP += 4000
                            return UseAbility(s, single_target.actor.id)
            if data.gauge.lilyStacks > 2 and data.gauge.bloodlilyStacks < 3:
                return UseAbility(18946, data.me.id)
        if data.gcd < 0.3:
            enemies = [Enemy(enemy, data) for enemy in data.valid_enemies if data.actor_distance_effective(enemy) < 31]
            enemies_25 = [enemy for enemy in enemies if enemy.dis < 26 and data.target_action_check(17790, enemy.enemy)]
            if not enemies_25: return
            if data.gauge.bloodlilyStacks > 2:
                for enemy in enemies_25: enemy.cal_aoe_targets(enemies)
                enemies_25_aoe = [enemy for enemy in enemies_25 if enemy.total_aoe > 1]
                if enemies_25_aoe:
                    target = max(enemies_25_aoe, key=lambda x: x.total_aoe)
                    if target.total_aoe > 2: return UseAbility(17793, target.enemy.id)
            if data.me.currentMP > 5000:
                t = min(enemies_25, key=dot_key)
                if dot_key(t)[0] < 5:
                    return UseAbility(17790, t.enemy.id)
