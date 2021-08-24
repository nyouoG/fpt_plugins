from functools import cache

from FFxivPythonTrigger.Utils import rotated_rect
from ..Strategy import *
from .. import Define


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return 1


def aoe_skill_id(data):
    return 18918 if data.combo_id == 18917 else 18919 if data.combo_id == 18918 else 18917


def single_skill_id(data):
    return 8793 if data.combo_id == 18916 else 8794 if data.combo_id == 8793 else 8798 if data.combo_id == 8794 else 18916


@cache
def aoe(me, target, dis):
    return rotated_rect(me.pos.x, me.pos.y, 2, dis, me.target_radian(target))


class DragoonPvpLogic(Strategy):
    name = "dragoon_pvp_logic"

    def common(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        aoe.cache_clear()
        enemies = None
        if data.gcd < 0.3:
            enemies = [(enemy, aoe(data.me, enemy, 10)) for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 10]
            if enemies:
                aoe_data = map(lambda x: (x[0], sum(map(lambda y: x[1].intersects(y[0].hitbox), enemies))), enemies)
                aoe_target, max_cnt = max(aoe_data, key=lambda x: x[1])
                if max_cnt > 1:
                    return UseAbility(aoe_skill_id(data), aoe_target.id)
            else:
                aoe_target = None
            enemies = [enemy for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 5]
            if enemies:
                return UseAbility(single_skill_id(data), min(enemies, key=lambda x: x.currentHP).id)
            elif aoe_target is not None:
                return UseAbility(aoe_skill_id(data), aoe_target.id)
            enemies = [enemy for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 15]
            if enemies: return UseAbility(8799, min(enemies, key=lambda x: x.currentHP).id)
        if not res_lv(data): return
        if data[18943] < 60 and data.me.currentHP / data.me.maxHP <= 0.7:
            return UseAbility(18943)
        if not data[18992]:
            enemies = [enemy for enemy in data.valid_enemies if
                       data.actor_distance_effective(enemy) <= 5 and enemy.currentHP < 4000 and (enemy.currentHP / enemy.maxHP) < 0.35]
            if enemies: return UseAbility(18992, min(enemies, key=lambda x: x.currentHP).id)
        if not data.gauge.stance: return
        if data.gauge.eyesAmount > 1 and ((not data[8805] and data.gauge.stance == 1) or (not data[8806] and data.gauge.stance == 2)):
            enemies = [(enemy, aoe(data.me, enemy, 15)) for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 15]
            aoe_data = list(map(lambda x: (x[0], sum(map(lambda y: x[1].intersects(y[0].hitbox), enemies))), enemies))
            if aoe_data:
                aoe_target, max_cnt = max(aoe_data, key=lambda x: x[1])
                return UseAbility(8805, aoe_target.id)
        can_1 = data[17730] < 15
        can_jmp = not data[17728]
        if can_1 or can_jmp:
            enemies = [enemy for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 20]
            if enemies:
                target = min(enemies, key=lambda x: x.currentHP)
                if target.currentHP <= 3000 and can_jmp:
                    return UseAbility(17728, target.id)
                elif can_1:
                    return UseAbility(17730, target.id)
