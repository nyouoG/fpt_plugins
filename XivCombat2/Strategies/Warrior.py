from FFxivPythonTrigger.Utils import circle
from ..Strategy import *
from .. import Define, Api
from time import perf_counter

"""
7388,摆脱,68
7386,猛攻,62
3552,泰然自若,58
48,守护,10
43,死斗,42
40,战栗,30
44,复仇,38

16464,原初的勇猛,76
3551,原初的直觉,56
7389,原初的解放,70
38,狂暴,6
52,战嚎,50

7387,动乱,64
46,飞斧,15

16465,狂魂,80
3549,裂石飞环,54
49,原初之魂,35

16463,混沌旋风,72
3550,地毁人亡,60
51,钢铁旋风,45

16462,秘银暴风,40
41,超压斧,10

42,暴风斩,26
45,暴风碎,50
37,凶残裂,4
31,重劈,1
"""

"""
86,狂暴,自身攻击必定暴击并且直击
90,暴风碎,攻击所造成的伤害提高
1897,原初的混沌,"地毁人亡变为混沌旋风 习得狂魂后追加效果：裂石飞环变为狂魂"
1177,原初的解放,兽魂不会消耗，自身攻击必定暴击并且直击，不受眩晕、睡眠、止步、加重和除特定攻击之外其他所有击退、吸引的效果影响
2227,原初的勇猛,自身的物理攻击命中时会吸收体力
"""


def count_enemy(data: LogicData):
    aoe = circle(data.me.pos.x, data.me.pos.y, 5)
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
    return int(data.max_ttk > 7)


class WarriorLogic(Strategy):
    name = "warrior_logic"

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)
        self.last_buff = 0

    def process_ability_use(self, data: LogicData, action_id: int, target_id: int) -> Optional[Tuple[int, int]]:
        if action_id in {16464, 7540, 7538}:
            mo_target = Api.get_mo_target()
            if mo_target: return action_id, mo_target.id

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        need_red = data.me.level >= 50 and (90 not in data.effects or data.effects[90].timer < 10)
        use_green = data.combo_id == 37 and (data.me.level < 50 or 90 in data.effects and data.effects[90].timer > 30)
        cnt = count_enemy(data)
        if 1177 in data.effects or not need_red and res_lv(data) and data.gauge.beast >= 50 and (
                86 in data.effects or 1177 in data.effects or 2227 in data.effects or
                data.gauge.beast > (80 if use_green else 90) or data[7389] < 2.5
        ):
            if cnt < 3:
                return UseAbility(49)
            elif data.me.level >= 45:
                return UseAbility(51)
        if data.combo_id == 41 and data.me.level >= 40:
            return UseAbility(16462)
        if data.combo_id == 37 and data.me.level >= 26:
            return UseAbility(42 if use_green else 45)
        if not need_red and cnt >= 2 and data.me.level >= 10:
            return UseAbility(41)
        if data.combo_id == 31 and data.me.level >= 4:
            return UseAbility(37)
        return UseAbility(31)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if res_lv(data) and (data.me.level < 50 or 90 in data.effects):
            s = 7389 if data.me.level >= 70 else 38
            if not data[s] and (data.gauge.beast < 50 or data.me.level < 70):
                return UseAbility(s)
            if not data[7387] and data.gauge.beast >= 20 and data[s] > 10:
                return UseAbility(7387)
            if data[52] < 60 and self.last_buff < perf_counter() - 0.5:
                if (1177 in data.effects or 86 in data.effects) and (data.me.level >= 80 or data.gauge.beast <= 50) or (
                        data[52] < 5 and data[s] > 20):
                    self.last_buff = perf_counter()
                    return UseAbility(52)
