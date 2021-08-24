from math import radians
from time import perf_counter

from FFxivPythonTrigger.Logger import info
from FFxivPythonTrigger.Utils import rotated_rect, sector, circle
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


bard_aoe_angle = radians(90)


class BardPvpLogic(Strategy):
    name = "bard_pvp_logic"

    def __init__(self, config):
        super().__init__(config)
        self.last_song = 0
        self.buff = 0

    def common(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        enemies_25 = [enemy for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 25]
        if not enemies_25: return
        if data.gcd < 0.3:
            if data.gauge.soulGauge >= 80:
                enemies = [(enemy, rotated_rect(data.me.pos.x, data.me.pos.y, 2, 25, data.me.target_radian(enemy))) for enemy in enemies_25]
                aoe_data = map(lambda x: (x[0], sum(map(lambda y: x[1].intersects(y[0].hitbox), enemies))), enemies)
                aoe_target, max_cnt = max(aoe_data, key=lambda x: x[1])
                if max_cnt > 1 or data.gauge.soulGauge > 99:
                    if self.buff < perf_counter() - 15:
                        self.buff = perf_counter()
                        return UseAbility(18955, data.me.id)
                    return UseAbility(17747, aoe_target.id)
            enemies = [(enemy, sector(data.me.pos.x, data.me.pos.y, 12, bard_aoe_angle, data.me.target_radian(enemy)))
                       for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 12]
            if enemies:
                aoe_data = map(lambda x: (x[0], sum(map(lambda y: x[1].intersects(y[0].hitbox), enemies))), enemies)
                aoe_target, max_cnt = max(aoe_data, key=lambda x: x[1])
                if max_cnt > 1: return UseAbility(18930, aoe_target.id)
            return UseAbility(17745, min(enemies_25, key=lambda x: x.currentHP).id)
        if data.me.currentHP / data.me.maxHP <= 0.7:
            if data[18943] <= 30: return UseAbility(18943, data.me.id)
        song = data.gauge.songType.value()
        if not song and self.last_song < perf_counter() - 1:
            if not data[8843]:
                self.last_song = perf_counter()
                return UseAbility(8843, min(enemies_25, key=lambda x: x.currentHP).id)
            if not data[8844]:
                self.last_song = perf_counter()
                return UseAbility(8844, min(enemies_25, key=lambda x: x.currentHP).id)
        else:
            if not data[8842] and song == 'minuet' and data.gauge.songProcs > (2 if data.gauge.songMilliseconds > 5000 else 0):
                return UseAbility(8842, min(enemies_25, key=lambda x: x.currentHP).id)
        if not data[18931]:
            enemies = [(enemy, circle(enemy.pos.x, enemy.pos.y, 5)) for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 30]
            aoe_data = map(lambda x: (x[0], sum(map(lambda y: x[1].intersects(y[0].hitbox), enemies))), enemies)
            aoe_target, max_cnt = max(aoe_data, key=lambda x: x[1])
            return UseAbility(18931, aoe_target.id)
        if not data[8841]:
            min_target = min(enemies_25, key=lambda x: x.currentHP)
            if min_target.currentHP < 3000: return UseAbility(8841, min_target.id)
        if data[8838] <= 15:
            return UseAbility(8838, min(enemies_25, key=lambda x: x.currentHP).id)
