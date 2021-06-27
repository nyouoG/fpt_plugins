from FFxivPythonTrigger.Utils import circle
from ..Strategy import *
from .. import Define

"""
16143：闪雷弹（15）
16137：利刃斩（1）
16139：残暴弹（4）
16145：迅连斩（26）
16141：恶魔切（10）
16149：恶魔杀（40）
16162：爆发击（30）
16163：命运之环（72）
16153：音速破（54）
16146：烈牙（60）
16147：猛兽爪（60）
16150：凶禽爪（60）
16155：续剑（70）
16144：危险领域（18/80)
16159：弓形冲波(62)
16138：无情(2)
16164：血壤（76）
"""
"""
1842：撕喉预备
1843：裂膛预备
1844：穿目预备
1831：无情
"""


def count_enemy(data: LogicData):
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    aoe = circle(data.me.pos.x, data.me.pos.y, 5)  # 六分
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 10)

def use_no_mercy(data:LogicData):
    if data.gcd < 2 and not data[16138] and (data[16164] < 10 or data[16164] > 25):
        if data.combo_id in [16139, 16141 if data.me.level >= 40 else -1]:
            if max(data[16159], data[16146], data[16153] < 4) and data.gauge.cartridges:
                return True
    return False

class GunbreakerLogic(Strategy):
    name = "gunbreaker_logic"

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_skill:  # 队列技能
            return data.config.get_query_skill()

        cartridges_full = data.combo_id in [16139, 16141 if data.me.level >= 40 else -1] and data.gauge.cartridges == 2
        cnt = count_enemy(data)
        res = res_lv(data)
        has_spec = 1842 in data.effects or 1843 in data.effects or 1844 in data.effects
        if data.target_distance > 3 and cnt < 3:
            return
        if use_no_mercy(data):
            return UseAbility(16138)
        if has_spec: return UseAbility(16155)  # 续剑
        if res and not data[16146] and (data[16138] > 5 or 1831 in data.effects) and data.gauge.cartridges and cnt < 3:
            return UseAbility(16146)  # 烈牙
        if not data[16153] and 1831 in data.effects:
            return UseAbility(16153)  # dot

        if data.gauge.continuationState == 1:
            return UseAbility(16147)
        if data.gauge.continuationState == 2:
            return UseAbility(16150)
        if data.combo_id == 16141 and data.gauge.cartridges < 2 and data.me.level >= 40:
            return UseAbility(16149)
        if data.combo_id == 16139 and data.gauge.cartridges < 2 and data.me.level >= 26:
            return UseAbility(16145)
        if data.me.level >= 72 or cnt < 3:
            if cartridges_full or ((1831 in data.effects or data[16164] < 3 and data[16138] > 10) and data.gauge.cartridges):
                return UseAbility(16162 if cnt < 3 else 16163)
        if data.combo_id == 16139 and data.me.level >= 26:
            return UseAbility(16145)
        if data.combo_id == 16137 and data.me.level >= 4:
            return UseAbility(16139)
        if data.combo_id == 16141 and data.me.level >= 40:
            return UseAbility(16149)
        return UseAbility(16137 if cnt < 2 or data.me.level < 10 else 16141)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability:
            return data.config.get_query_ability()
        has_spec = 1842 in data.effects or 1843 in data.effects or 1844 in data.effects
        if data.target_distance > 3: return
        if has_spec: return UseAbility(16155)
        if not res_lv(data): return
        if use_no_mercy(data):
            if data.config.ability_cnt and data.gcd > 1.5:
                return
            elif data.gcd <= 1.5:
                return UseAbility(16138)
        if not data[16164] and data[16138] > 10 and data.combo_id != 16139 and not data.gauge.cartridges:
            return UseAbility(16164)
        if not data[16144] and (data[16138] > 10 or 1831 in data.effects):
            return UseAbility(16144)
        if not data[16159] and 1831 in data.effects:
            return UseAbility(16159)
