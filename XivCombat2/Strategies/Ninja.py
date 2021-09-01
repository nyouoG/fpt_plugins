import time
from functools import lru_cache

from FFxivPythonTrigger.Utils import circle
from ..Strategy import *
from .. import Define

"""
2240,双刃旋,1
2241,残影,2
2242,绝风,4
7541,内丹,8
2245,隐遁,10
7863,扫腿,10
7542,浴血,12
2247,飞刀,15
2248,夺取,15
2258,攻其不备,18
7549,牵制,22
2255,旋风刃,26
2257,影牙,30
2259,天之印,30
2260,忍术,30
2265,风魔手里剑,30
2272,通灵之术,30
18805,天之印,30
18873,风魔手里剑,30
18874,风魔手里剑,30
18875,风魔手里剑,30
7548,亲疏自行,32
2261,地之印,35
2266,火遁之术,35
2267,雷遁之术,35
18806,地之印,35
18876,火遁之术,35
18877,雷遁之术,35
2254,血雨飞花,38
2262,缩地,40
2263,人之印,45
2268,冰遁之术,45
2269,风遁之术,45
2270,土遁之术,45
2271,水遁之术,45
18807,人之印,45
18878,冰遁之术,45
18879,风遁之术,45
18880,土遁之术,45
18881,水遁之术,45
2264,生杀予夺,50
7546,真北,50
16488,八卦无刃杀,52
3563,强甲破点突,54
3566,梦幻三段,56
2246,断绝,60
7401,通灵之术·大虾蟆,62
7402,六道轮回,68
7403,天地人,70
16489,命水,72
16491,劫火灭却之术,76
16492,冰晶乱流之术,76
16493,分身之术,80
17413,双刃旋,80
17414,绝风,80
17415,旋风刃,80
17416,影牙,80
17417,强甲破点突,80
17418,飞刀,80
17419,血雨飞花,80
17420,八卦无刃杀,80
"""
"""
1955,"断绝预备","可以发动断绝"
496,"结印","结成手印准备发动忍术"
507,"水遁之术","不用隐遁身形也能够发动需要在隐遁状态下发动的技能"
501,"土遁之术","产生土属性攻击区域"
497,"生杀予夺","可以发动忍术并且忍术的威力提升"
1186,"天地人","可以连发忍术"
1250,"真北","无视自身技能的方向要求"
"""

"""
ninja_huton_time 续风遁的时间 默认20  
ninja_combo      手动要求打一个忍术（类型参考 combos）  
check_position   是否检测身位 默认true  
"""
TEN = 3  # 天
CHI = 2  # 地
JIN = 1  # 人


def get_mudra(effects: dict):
    if 496 not in effects:
        return ""
    p = effects[496].param
    s = ''
    for i in range(4):
        m = (p >> (i * 2)) & 0b11
        if m:
            s += str(m)
        else:
            break
    return s


m2s = {
    TEN: 2259,
    CHI: 2261,
    JIN: 2263,
}


def c(*mudras: int):
    # return sum(m << (i * 2) for i, m in enumerate(mudras))
    # return ''.join(map(str, mudras))
    return [m2s[m] for m in mudras]


combos = {
    'normal': c(TEN),
    'fire': c(CHI, TEN),
    'thunder': c(TEN, CHI),
    'ice': c(TEN, JIN),
    'wind': c(JIN, CHI, TEN),
    'ground': c(JIN, TEN, CHI),
    'water': c(TEN, CHI, JIN),
    'water_multi': c(CHI, TEN, JIN),
}


def count_enemy(data: LogicData, skill_type: int):
    """
    :param skill_type: 0:普通 1:蛤蟆 2:火遁
    """
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    if skill_type == 0:
        aoe = circle(data.me.pos.x, data.me.pos.y, 5)
    elif skill_type == 1:
        aoe = circle(data.target.pos.x, data.target.pos.y, 6)
    else:
        aoe = circle(data.target.pos.x, data.target.pos.y, 5)
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 5)


def get_setting_huton_time(data: LogicData):
    return float(data.config.custom_settings.setdefault('ninja_huton_time', '20'))


class NinjaLogic(Strategy):
    name = "ninja_logic"
    fight_only = False

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)
        self.effects_temp = dict()
        self.combo = []
    def process_ability_use(self, data: LogicData, action_id: int, target_id: int) -> Optional[Tuple[int, int]]:
        pass

    def have_effect(self, data: LogicData, effect_id: int, allow_time=2):
        return effect_id in data.effects or self.effects_temp.setdefault(effect_id, 0) > time.time() - allow_time

    def set_effect(self, effect_id: int):
        self.effects_temp[effect_id] = time.time()

    @lru_cache
    def check_position(self, data: LogicData, position: str):
        if data.target.is_positional and data.config.custom_settings.setdefault('check_position', 'true') == 'true':
            return data.target.target_position(data.me) == position or self.have_effect(data, 1250)
        return True

    def can_ground(self, data: LogicData):
        return not self.have_effect(data, 501, 5)

    def get_ground(self):
        self.set_effect(501)
        return combos['ground'].copy()

    def common(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.gcd < 0.3 and not self.combo:
            combo_use = data.config.custom_settings.setdefault('ninja_combo', '')
            if combo_use in combos:
                if combo_use == "ground": self.set_effect(501)
                data.config.custom_settings['ninja_combo'] = ''
                self.combo = combos[combo_use].copy()
        if self.combo:
            return UseAbility(self.combo.pop(0))
        elif 496 in data.effects:
            return UseAbility(2260)

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_skill:  # 队列技能
            return data.config.get_query_skill()
        if not data.valid_enemies: return

        _res_lv = res_lv(data)
        cnt0 = count_enemy(data, 0)
        cnt2 = count_enemy(data, 2)
        use_res = _res_lv and (data[2258] > 45 or data.me.level < 45 or cnt0 > 2)

        if 497 in data.effects:
            if data.me.level >= 76:
                self.combo = combos['fire'].copy() if cnt2 > 1 else combos['ice'].copy()
            elif cnt2 > 1:
                self.combo = self.get_ground() if data.max_ttk > 15 and self.can_ground(data) else combos['fire'].copy()
            else:
                self.combo = combos['thunder'].copy()
        elif 1186 in data.effects:
            self.combo = combos['water'].copy() if cnt2 < 2 else self.get_ground() if self.can_ground(data) else combos['water_multi'].copy()
        elif data[2259] <= 20:
            if data.me.level >= 45:
                if not data.gauge.hutonMilliseconds:
                    self.combo = combos['wind'].copy()
                elif _res_lv:
                    if (data[2258] < 20 or not data[16489]) and 507 not in data.effects and (data[2259] < 5 or data[2258] < 5 or data.target_distance > 6):
                        self.combo = combos['water'].copy()
                    elif cnt0 > 2 and data.max_ttk > 15 and self.can_ground(data):
                        self.combo = self.get_ground()
            if not self.combo and _res_lv and (use_res or data[2259] < 5 or data.target_distance > 6):
                if data.me.level >= 35:
                    self.combo = combos['fire'].copy() if cnt2 > 1 else combos['thunder'].copy()
                else:
                    self.combo = combos['normal'].copy()
        if self.combo: return UseAbility(self.combo.pop(0))
        if cnt0 > 2 and data.me.level >= 38:
            return UseAbility(16488 if data.combo_id == 2254 and data.me.level >= 52 else 2254)
        if data.target_distance > 3: return
        if not data[2257] and use_res: return UseAbility(2257)
        if data.combo_id == 2242 and data.me.level >= 26:
            is_side = self.check_position(data, "SIDE")
            is_back = self.check_position(data, "BACK")
            if data.me.level >= 54:
                huton_time = data.gauge.hutonMilliseconds / 1000
                must_huton = huton_time and huton_time < get_setting_huton_time(data) and data.max_ttk > huton_time
                if is_back and not must_huton:
                    return UseAbility(2255)
                elif is_side or must_huton:
                    if not is_side and data[7546] <= 45 and data[7546] - data[2258] <= 0:
                        self.set_effect(1250)
                        return UseAbility(7546)  # 真北
                    return UseAbility(3563)
            if not is_back and data[7546] <= 45 and (data[7546] - data[2258] <= 0 or data.me.level < 45):
                self.set_effect(1250)
                return UseAbility(7546)  # 真北
            return UseAbility(2255)
        if data.combo_id == 2240 and data.me.level >= 4:
            return UseAbility(2242)
        return UseAbility(2240)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:

        if data.config.query_ability:
            return data.config.get_query_ability()
        if not data.valid_enemies: return
        _res_lv = res_lv(data)
        cnt0 = count_enemy(data, 0)
        if not _res_lv or data.target_distance > 25: return
        use_res = _res_lv and (data[2258] > 45 or data.me.level < 45 or cnt0 > 2)
        if not data[16493] and data.gauge.ninkiAmount >= 50:
            return UseAbility(16493)  # 分身
        if data.target_distance <= 3:
            if not data[2248] and data.gauge.ninkiAmount <= 60 and data[2258] < 5:
                return UseAbility(2248)  # 夺取
            if data.gauge.ninkiAmount >= 50 and (
                    use_res or data.gauge.ninkiAmount > (50 if not data[16489] and 507 in data.effects else 60 if not data[2248] else 80)):
                return UseAbility(7402) if data.me.level >= 68 and count_enemy(data, 1) < 2 else UseAbility(7401)  # 六道
            if not data[2258] and data[16493] and 507 in data.effects:
                if not self.check_position(data, "BACK") and data[7546] < 45:
                    self.set_effect(1250)
                    return UseAbility(7546)  # 真北
                return UseAbility(2258)  # 背刺
            if not data[3566] and use_res:
                return UseAbility(3566)  # 梦幻三段
            if data.me.level >= 60 and 1955 in data.effects:
                return UseAbility(2246)  # 断绝
        if not data[2264] and use_res:
            return UseAbility(2264)  # 生杀
        if not data[7403] and use_res and not data.is_moving:
            return UseAbility(7403)  # 天地人
        if not data[16489] and data[2258] > 20 and 507 in data.effects and data.gauge.ninkiAmount <= 50:
            return UseAbility(16489)  # 命水
