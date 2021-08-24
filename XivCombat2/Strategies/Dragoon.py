from FFxivPythonTrigger.Utils import rotated_rect
from ..Strategy import *
from .. import Define

"""
7541,内丹,8
7863,扫腿,10
7542,浴血,12
7549,牵制,22
7548,亲疏自行,32
7546,真北,50

75,精准刺,1
78,贯通刺,4
83,龙剑,6
90,贯穿尖,15
87,开膛枪,18
84,直刺,26
85,猛枪,30
92,跳跃,30
94,回避跳跃,35
86,死天枪,40
95,破碎冲,45
88,樱花怒放,50
96,龙炎冲,50
3557,战斗连祷,52
3553,苍天龙血,54
3554,龙牙龙爪,56
3556,龙尾大回旋,58
3555,武神枪,60
7397,音速刺,62
7398,巨龙视线,66
7399,幻象冲,68
7400,死者之岸,70
16477,山境酷刑,72
16478,高跳,74
16479,龙眼雷电,76
16480,坠星冲,80
"""
"""
118,樱花怒放,体力逐渐减少
802,龙牙龙爪效果提高,可以发动龙牙龙爪
803,龙尾大回旋效果提高,可以发动龙尾大回旋
1243,幻象冲预备,可以发动幻象冲
1914,开膛枪,攻击所造成的伤害提高
1863,龙眼雷电预备,可以发动龙眼雷电
"""


def cnt_enemy(data: LogicData) -> int:
    aoe = rotated_rect(data.me.pos.x, data.me.pos.y, 2, 10, data.me.target_radian(data.target))
    cnt = sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))
    if not cnt: return 0
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    return cnt


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 5)


combo_buff = {802, 803, 1863}
combo_lv = {75: 4, 78: 26, 87: 50}


class DragoonLogic(Strategy):
    name = "dragoon_logic"

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        cnt = cnt_enemy(data)
        has_next = set(data.effects.keys()).intersection(combo_buff) or data.combo_id in combo_lv and data.me.level >= combo_lv[data.combo_id]
        if data.me.level >= 40 and cnt and (cnt >= 3 or data.target_distance > 4 and not has_next):
            if data.combo_id == 7397 and data.me.level >= 72: return UseAbility(16477)
            if data.combo_id == 86 and data.me.level >= 62: return UseAbility(7397)
            return UseAbility(86)
        if data.target_distance > 4: return
        if 802 in data.effects: return UseAbility(3554)
        if 803 in data.effects: return UseAbility(3556)
        if data.combo_id == 78 and data.me.level >= 26: return UseAbility(84)
        if data.combo_id == 87 and data.me.level >= 50: return UseAbility(88)
        if data.combo_id == 75 and data.me.level >= 4:
            if data.me.level >= 18:
                t = 14 if data.me.level >= 56 else 9 if data.me.level >= 26 else 6
                if 1914 not in data.effects or data.effects[1914].timer < t:
                    return UseAbility(88)
                if data.me.level >= 50 and data.time_to_kill_target >= 20:
                    t_effect = data.target.effects.get_dict(source=data.me.id)
                    if 118 not in t_effect or t_effect[118].timer < t:
                        return UseAbility(88)
            return UseAbility(78)
        return UseAbility(75)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if not res_lv(data): return
        if not (data[3553] or data.gauge.blood_or_life_ms) and data.gauge.stance != 2:
            return UseAbility(3553)
        if not data[83] and data.combo_id == (78 if data.me.level >= 26 else 75): return UseAbility(83)
        if not data[85] and (data.combo_id == 78 or data.combo_id == 87 or cnt_enemy(data) >= 3) and data.max_ttk > 15: return UseAbility(85)
        jump_distance = float(data.config.custom_settings.setdefault('drg_jump', '0'))
        if 1243 in data.effects: return UseAbility(7399)
        if not data[7400] and data.gauge.stance == 2: return UseAbility(7400)
        if data.target_distance <= jump_distance <= 20:
            if not data[92]: return UseAbility(92)
            if not data[96]: return UseAbility(96)
            if not data[95]: return UseAbility(95)
            if not data[16480] and data.gauge.stance == 2: return UseAbility(16480)
        if not data[3555]: return UseAbility(3555)
