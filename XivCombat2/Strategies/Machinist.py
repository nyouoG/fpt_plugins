from math import radians

from FFxivPythonTrigger.Utils import sector
from ..Strategy import *
from .. import Define

"""
2866：分裂弹
2868：独头弹
2872：热弹
2876：整备
2874：虹吸弹
2870：散射
2873：狙击弹
17209：超荷
7410：热冲击
2864：炮塔
2878：野火
2890：弹射
16497：自动弩
16498：钻头
7414：枪管加热
16499：毒菌
"""

mch_aoe_angle = radians(90)


def is_single(data: LogicData) -> bool:
    if data.config.single == Define.FORCE_SINGLE:
        return True
    elif data.config.single == Define.FORCE_MULTI:
        return False
    cnt = 0
    mch_aoe = sector(data.me.pos.x, data.me.pos.y, 12, mch_aoe_angle, data.me.target_radian(data.target))
    for enemy in data.valid_enemies:
        if mch_aoe.intersects(enemy.hitbox):
            cnt += 1
            if cnt > 2: return False
    return True


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(1e+10 > data.max_ttk > 5)


class MachinistLogic(Strategy):
    name = "machinist_logic"

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        hsid = 2872 if data.me.level < 76 else 16500
        single = is_single(data)
        res_use = res_lv(data)
        if data.config.query_skill:
            return data.config.get_query_skill()
        if data.target_distance > 25:
            return
        if data[2876] or not res_use:
            if data.gcd >= data[16498]: return UseAbility(16498 if single or data.me.level < 72 else 16498)
            if data.gcd >= data[hsid]: return UseAbility(hsid)
        if single or data.target_distance > 12 or data.me.level < 18:
            if data.gauge.overheatMilliseconds and data.me.level >= 35:
                return UseAbility(7410)
            elif data.combo_id == 2866 and data.me.level >= 2:
                return UseAbility(2868)
            elif data.combo_id == 2868 and data.me.level >= 26:
                return UseAbility(2873)
            else:
                return UseAbility(2866)
        else:
            return UseAbility(16497 if data.gauge.overheatMilliseconds and data.me.level >= 52 else 2870)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        hsid = 2872 if data.me.level < 76 else 16500
        res_use = res_lv(data)
        if data.config.query_ability:
            return data.config.get_query_ability()
        if data.target_distance > 25:
            return
        if min(data[2874], data[2890]) < 15:
            return UseAbility(2874) if data[2874] <= data[2890] else UseAbility(2890)
        if not res_use: return
        if data.gauge.battery >= 90:
            return UseAbility(2864)
        if not data[2876]:
            if data[16498] < data.gcd:
                data.reset_cd(16498)
                return UseAbility(2876)
            elif data[hsid] < data.gcd:
                data.reset_cd(hsid)
                return UseAbility(2876)
        can_over = not data.gauge.overheatMilliseconds and data[16498] > 8 and data[hsid] > 8 and data.combo_remain > 11 and data.gauge.heat >= 50
        if can_over and not data[2878] and not data.config.ability_cnt:
            return UseAbility(2878)
        if can_over and data[2878] > 8:
            if data.config.ability_cnt and data.gcd > 1.3:
                return
            elif data.gcd <= 1.3:
                return UseAbility(17209)
        if data.gauge.heat < 50 and not data[7414]: return UseAbility(7414)
        if min(data[2874], data[2890]) < 60:
            return UseAbility(2874) if data[2874] <= data[2890] else UseAbility(2890)
        if data.gauge.battery >= 50:
            return UseAbility(2864)
