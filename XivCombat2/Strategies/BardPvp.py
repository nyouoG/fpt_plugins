from functools import cached_property
from math import radians
from time import perf_counter

from FFxivPythonTrigger.Logger import info
from FFxivPythonTrigger.Utils import rotated_rect, sector, circle
from ..Strategy import *
from .. import Define, Api, PvpDmgBuff


class UseAbility(UseAbility):
    def __init__(self, ability_id: int, target=None):
        super().__init__(ability_id, target.id if target else None)
        if target is not None and target != Api.get_me_actor(): Api.set_current_target(target)


bard_aoe_angle = radians(90)

lb_skill_ids = {3360, 3361, 4249}


class Enemy(object):
    def __init__(self, actor):
        self.actor = actor
        self.tbuff = 0
        self.aoe1_total = 0
        self.aoe2_total = 0
        self.aoe3_total = 0

    @property
    def hpp(self):
        return self.actor.currentHP / self.actor.maxHP

    @cached_property
    def effective_hp(self):
        self.tbuff = PvpDmgBuff.get_tbuff(self.actor)
        return ((self.actor.shield_percent * self.actor.maxHP / 100) + self.actor.currentHP) / self.tbuff

    @cached_property
    def hitbox(self):
        return circle(self.actor.pos.x, self.actor.pos.y, 0.1)

    def cal_aoe2(self, me, enemies: list['Enemy']):
        area = sector(me.pos.x, me.pos.y, 12, bard_aoe_angle, me.target_radian(self.actor))
        self.aoe2_total = sum(area.intersects(enemy.hitbox) for enemy in enemies)
        return self.aoe2_total

    @cached_property
    def aoe1_dmg(self):
        return 600 + 1200 * self.hpp

    def cal_aoe1(self, enemies: list['Enemy']):
        area = circle(self.actor.pos.x, self.actor.pos.y, 5)
        self.aoe1_total = sum(enemy.aoe1_dmg for enemy in enemies if area.intersects(enemy.hitbox))
        return self.aoe1_total

    def cal_aoe3(self, me, enemies: list['Enemy']):
        area = rotated_rect(me.pos.x, me.pos.y, 1, 25, me.target_radian(self.actor))
        self.aoe3_total = sum(area.intersects(enemy.hitbox) for enemy in enemies)
        return self.aoe3_total


class BardPvpLogic(Strategy):
    name = "bard_pvp_logic"

    def __init__(self, config):
        super().__init__(config)
        self.last_song = 0

    def common(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        enemies = [Enemy(enemy) for enemy in data.valid_enemies if data.actor_distance_effective(enemy) <= 35 and enemy.currentHP > 1]
        if not enemies: return
        enemies_25 = [enemy for enemy in enemies if data.target_action_check(17745, enemy.actor)]
        if not enemies_25: return
        min_target = min(enemies_25, key=lambda e: e.effective_hp)
        buff = PvpDmgBuff.get_buff(data.me)
        song = data.gauge.songType.value()

        """集中"""
        buff_cd = data.pvp_skill_cd(18955)
        can_use_buff = buff_cd is not None and not buff_cd
        has_buff = buff_cd is not None and (buff > 13 or 2186 in data.effects)
        cal_buff = has_buff or can_use_buff

        """恰药"""
        if data[18943] <= 30:
            medic = 3000 + 3000 * (1 - data.me.currentHP / data.me.maxHP)
            if data.me.maxHP - data.me.currentHP >= medic:
                data.me.currentHP += int(medic)
                return UseAbility(18943, data.me)

        """預計算絶峰"""
        if data.gauge.soulGauge >= 50:
            soul = 24 * buff * data.gauge.soulGauge
            soul_c = soul * 1.5 if has_buff else soul
        else:
            soul = 0
            soul_c = 0

        """抢头"""
        kill_skills = []
        if not data[8842] and song == 'minuet':  # 完美音调
            kill_skills.append((8842, data.gauge.songProcs * 600 * buff))
        if song and data[8838] <= 15:  # 九天
            kill_skills.append((8838, 1000 * buff))
        if data.gcd < 0.3:
            kill_skills.append((17745, 1200 * buff * (1.5 if has_buff else 1)))  # 爆发射击
            kill_skills.append((17747, soul_c))  # 绝峰箭

        if kill_skills:
            max_skill_id, max_skill_dmg = max(kill_skills, key=lambda x: x[1])
            if max_skill_dmg >= min_target.effective_hp:
                if data.config.custom_settings.setdefault('debug_output', 'false') == 'true':
                    info('bard_k', f"{min_target.actor.Name}|{min_target.actor.currentHP}|{max_skill_id}|{int(max_skill_dmg / min_target.tbuff)}")
                return UseAbility(max_skill_id, min_target.actor)

        if not data[8841]:  # 侧风
            dmg = (1600 * (1 - min_target.hpp) + 800) * buff
            if dmg >= min_target.effective_hp:
                if data.config.custom_settings.setdefault('debug_output', 'false') == 'true':
                    info('bard_k', f"{min_target.actor.Name}|{min_target.actor.currentHP}|侧风|{int(dmg / min_target.tbuff)}")
                min_target.actor.currentHP = 0
                return UseAbility(8841, min_target.actor)

        if data.gcd < 0.7 and can_use_buff and soul * 1.6 >= min_target.effective_hp:  # 集中
            return UseAbility(18955, data.me)

        """断lb"""
        if not data[17680]:
            for enemy in enemies_25:
                if enemy.actor.CastingID in lb_skill_ids:
                    return UseAbility(17680, enemy.actor)

        """影噬"""
        if not data[18931]:
            target = max(enemies_25, key=lambda x: x.cal_aoe1(enemies))
            if target.aoe1_total >= 4800:
                return UseAbility(18931, target.actor)

        if (not song or (song == 'paeon' and data.gauge.songProcs > 3 and data[8844] < 30)) and self.last_song < perf_counter() - 1:
            """唱歌"""
            if not data[8843]:  # 放浪神
                self.last_song = perf_counter()
                return UseAbility(8843, min_target.actor)
            if not data[8844]:  # 贤者
                self.last_song = perf_counter()
                return UseAbility(8844, min_target.actor)

        elif not data[8842] and song == 'minuet' and data.gauge.songMilliseconds < 1500 and data.gauge.songProcs:
            """完美音调即将过期"""
            return UseAbility(8842, min_target.actor)

        """绝峰箭"""
        if data.gcd < (0.7 if cal_buff else 0.3) and data.gauge.soulGauge >= 50:
            aoe3_target = max(enemies_25, key=lambda e: e.cal_aoe3(data.me, enemies))
            if aoe3_target.aoe3_total * 24 * data.gauge.soulGauge >= 10000:
                return UseAbility((18955 if can_use_buff else 17747), aoe3_target.actor)
            if has_buff:
                return UseAbility(17747, min_target.actor)

        if data.gcd > 0.3:
            """九天防止溢出"""
            if data[8838] < 2 and data.gauge.songProcs < (3 if song == 'minuet' else 4):
                return UseAbility(8838, min_target.actor)
            return

        """尝试aoe"""
        try:
            aoe_target = max(
                (enemy for enemy in enemies_25 if data.target_action_check(18930, enemy.actor)),
                key=lambda e: e.cal_aoe2(data.me, enemies)
            )
        except ValueError:
            pass
        else:
            if aoe_target.aoe2_total > 2:
                return UseAbility(18930, aoe_target.actor)

        """普通gcd"""
        return UseAbility(17745, min_target.actor)
