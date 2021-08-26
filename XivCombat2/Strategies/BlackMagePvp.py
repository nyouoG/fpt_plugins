from time import perf_counter

import member as member

from FFxivPythonTrigger.Logger import info
from FFxivPythonTrigger.Utils import circle
from ..Strategy import *
from .. import Api


class UseAbility(UseAbility):
    def __init__(self, ability_id: int, target=None):
        super().__init__(ability_id, target.id if target else None)
        if target is not None and target != Api.get_me_actor(): Api.set_current_target(target)


"""
雷云 1365 可以咏唱暴雷或霹雷
震雷 2075 受到持续伤害
闪雷 1324 受到持续伤害
"""


def aoe(data):
    if (data.me.currentMP >= 4000 and data.gauge.umbralStacks > 0) or data.me.currentMP >= 10000:
        return 8866
    return 8867


def single(data):
    if data.me.currentMP >= 2000 and data.gauge.umbralStacks > 0:
        return 8863
    return 8864


class Enemy(object):
    def __init__(self, enemy, data: LogicData):
        self.enemy = enemy
        self.effects = enemy.effects.get_dict(source=data.me.id)
        if 2075 in self.effects:
            self.thunder = self.effects[2075].timer
        elif 1324 in self.effects:
            self.thunder = self.effects[1324].timer
        else:
            self.thunder = 0
        self.hitbox = circle(enemy.pos.x, enemy.pos.y, 0.1)
        self.dis = data.actor_distance_effective(enemy)
        self.total_aoe = 0
        self.total_aoe_thunder = 0
        self.total_aoe_non_thunder = 0

    def cal_aoe_targets(self, enemies: list['Enemy']):
        aoe_area = circle(self.enemy.pos.x, self.enemy.pos.y, 5)
        for enemy in enemies:
            if aoe_area.intersects(enemy.hitbox):
                if enemy.thunder:
                    self.total_aoe_thunder += 1
                else:
                    self.total_aoe_non_thunder += 1
        self.total_aoe = self.total_aoe_thunder + self.total_aoe_non_thunder


def get_nearby_alliance(data: LogicData, target):
    return sum(map(lambda a_m: target.absolute_distance_xy(a_m) < 10, data.valid_alliance))


def get_nearby_enemy(data: LogicData, target):
    return sum(map(lambda a_m: target.absolute_distance_xy(a_m) < 30, data.valid_enemies))


def get_nearest_enemy_distance(data: LogicData, target):
    d = list(map(lambda a_m: target.absolute_distance_xy(a_m) < 30, data.valid_enemies))
    if not d: return 500
    return min(d)


class BlackMagePvpLogic(Strategy):
    name = "black_mage_pvp_logic"
    fight_only = False

    def __init__(self, config):
        super().__init__(config)
        self.buff = 0

    def process_ability_use(self, data: LogicData, action_id: int, target_id: int) -> Optional[Tuple[int, int]]:
        if action_id == 8869:
            move_targets = [member for member in data.valid_party if member.id != data.me.id and
                            data.actor_distance_effective(member) < 26 and data.target_action_check(8869, member)]
            if move_targets:
                _move_targets = [member for member in move_targets if get_nearby_alliance(data, member) > 4]
                if _move_targets: move_targets = _move_targets
                # move_target = max(move_targets, key=lambda target: get_nearest_enemy_distance(data, target))
                move_target = min(move_targets, key=lambda target: get_nearby_enemy(data, target))
                if get_nearest_enemy_distance(data, move_target) < get_nearest_enemy_distance(data, data.me):
                    return action_id, data.me.id
                return action_id, move_target.id
        elif action_id == 17775:
            enemies = [Enemy(enemy, data) for enemy in data.valid_enemies if data.actor_distance_effective(enemy) < 31]
            enemies_25 = [enemy for enemy in enemies if enemy.dis < 26 and data.target_action_check(8858, enemy.enemy)]
            if not enemies_25: return
            for enemy in enemies_25: enemy.cal_aoe_targets(enemies)
            enemies_25_aoe = [enemy for enemy in enemies if enemy.total_aoe > 1]
            target = max(enemies_25_aoe, key=lambda x: x.total_aoe) if enemies_25_aoe else min(enemies_25, key=lambda x: x.dis)
            return 17775, target.enemy.id

    def common(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.me.currentHP / data.me.maxHP <= 0.7 and data[18943] <= 30:
            return UseAbility(18943, data.me)
        if data.gcd > 0.4: return
        enemies = [Enemy(enemy, data) for enemy in data.valid_enemies if data.actor_distance_effective(enemy) < 31]
        enemies_25 = [enemy for enemy in enemies if enemy.dis < 26 and data.target_action_check(8858, enemy.enemy)]
        if not enemies_25: return
        for enemy in enemies_25: enemy.cal_aoe_targets(enemies)
        enemies_25_aoe = [enemy for enemy in enemies if enemy.total_aoe > 1]
        has_speed = 1987 in data.effects or self.buff > perf_counter() - 1
        if enemies_25_aoe:
            if 1365 in data.effects:
                aoe_target = max(enemies_25_aoe, key=lambda x: (x.total_aoe, x.total_aoe_non_thunder))
                if aoe_target.total_aoe > (2 if data.effects[1365].timer > 5 else 1):
                    return UseAbility(18936, aoe_target.enemy)
            enemies_25_thunder = [enemy for enemy in enemies_25_aoe if enemy.total_aoe_thunder]
            if enemies_25_thunder:
                aoe_target = max(enemies_25_thunder, key=lambda x: x.total_aoe)
                if data.gauge.foulCount and (data.gauge.foulCount > 1 or aoe_target.total_aoe > 3):
                    return UseAbility(8865, aoe_target.enemy)
                if self.buff < perf_counter() - 15 and data.me.currentMP >= 4000 and data.gauge.umbralStacks > 0 and aoe_target.total_aoe > 2:
                    self.buff = perf_counter()
                    return UseAbility(17685)
                if has_speed:
                    return UseAbility(aoe(data), aoe_target.enemy)
            aoe_target = max(enemies_25_aoe, key=lambda x: (x.total_aoe_non_thunder, x.total_aoe))
            if aoe_target.total_aoe_non_thunder > 1 and data.gauge.umbralMilliseconds > 3000 and data.gauge.umbralStacks > 0:
                return UseAbility(18935, aoe_target.enemy)
            if not data.is_moving:
                enemies_20_aoe = [enemy for enemy in enemies if enemy.dis < 23]
                if enemies_20_aoe:
                    aoe_target = max(enemies_20_aoe, key=lambda x: (x.total_aoe_thunder, x.total_aoe))
                    return UseAbility(aoe(data), aoe_target.enemy)
        single_target = min(enemies_25, key=lambda x: x.enemy.currentHP)
        if data.gauge.foulCount and single_target.enemy.currentHP < 3000:
            return UseAbility(17774, single_target.enemy)
        target_with_thunder = [enemy for enemy in enemies_25 if enemy.thunder > 3]
        if target_with_thunder:
            single_target = min(target_with_thunder, key=lambda x: x.enemy.currentHP)
        if has_speed:
            if data.gauge.umbralStacks:
                return UseAbility(single(data), single_target.enemy)
            else:
                return UseAbility(aoe(data), single_target.enemy)
        if 1365 in data.effects and data.effects[1365].timer < 5:
            return UseAbility(8861, single_target.enemy)
        if not (target_with_thunder or data.gauge.umbralMilliseconds < 3000) and enemies_25_aoe:
            return UseAbility(18935, max(enemies_25_aoe, key=lambda x: (x.total_aoe_non_thunder, x.total_aoe)).enemy)
        if not data.is_moving and data.gauge.umbralMilliseconds > 3000:
            return UseAbility(single(data), single_target.enemy)
        if (data.me.currentMP >= 5000 and data.gauge.umbralStacks > 0) or data.me.currentMP >= 10000:
            return UseAbility(8858, single_target.enemy)
        return UseAbility(8859, single_target.enemy)
