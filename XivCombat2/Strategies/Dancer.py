from time import perf_counter

from FFxivPythonTrigger.Utils import circle

from ..Strategy import *
from .. import Define

"""
15989：瀑泻（1）
15990：喷泉（2）
15991：逆瀑泻（20）
15992：坠喷泉（40）
15993：风车（15）
15994：落刃雨（25）
15995：升风车（35）
15996：落血雨（45）
16007：扇舞·序（30）
16008：扇舞·破（50）
16009：扇舞·急（66）
15997：标准舞步（15）
15998：技巧舞步（70）
16005：剑舞（76）
16011：直爆舞
16013：百花
"""
"""
1814,逆瀑泻预备
1815,坠喷泉预备
1816,升风车预备
1817,落血雨预备
1818,标准舞步
1819,技巧舞步
1820,扇舞·急预备
1821,标准舞步结束
1822,技巧舞步结束
"""


def step_to_skill(step):
    return 15998 + step.raw_value if step.raw_value > 0 else None


def count_enemy(data: LogicData, skill_type: int):
    # 1：普通aoe，2：大小舞
    aoe = circle(data.me.pos.x, data.me.pos.y, 5 if skill_type == 1 else 15)
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 9)


class DancerLogic(Strategy):
    name = "dancer_logic"

    def __init__(self, config: 'CombatConfig'):

        super().__init__(config)
        self.last_feather = perf_counter()

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if 1818 in data.effects:  # 小舞
            cnt2 = count_enemy(data, 2)
            if data.gauge.currentStep < 2:
                return UseAbility(step_to_skill(data.gauge.step[data.gauge.currentStep]))
            elif cnt2 or data.effects[1818].timer < 2:
                return UseAbility(15997)
            else:
                return
        elif 1819 in data.effects:  # 大舞
            cnt2 = count_enemy(data, 2)
            if data.gauge.currentStep < 4:
                return UseAbility(step_to_skill(data.gauge.step[data.gauge.currentStep]))
            elif cnt2 or data.effects[1819].timer < 2:
                return UseAbility(15998)
            else:
                return
        if data.config.query_skill:  # 队列技能
            return data.config.get_query_skill()

        if data.target_distance > 25: return

        if (1821 not in data.effects or data.effects[1821].timer < 5) and not data[15997]:
            return UseAbility(15997)  # 没有小舞状态优先小舞

        res = res_lv(data)

        if res and not data[15998]:  # 开始大舞
            return UseAbility(15998)
        if data.gauge.esprit > 85 and res:  # 剑舞防止溢出
            return UseAbility(16005)

        cnt1 = count_enemy(data, 1)
        s3, sr, a3, ar = list(map(lambda e: 0 if e not in data.effects else data.effects[e].timer, [
            1815,  # 坠喷泉 s3 15992
            1814,  # 逆瀑泻 sr 15991
            1817,  # 落血雨 a3 15996
            1816,  # 升风车 ar 15995
        ]))

        if cnt1 > 1:  # 剩余两个gcd的触发技能优先使用
            if a3 and a3 < 6: return UseAbility(15996)
            if ar and ar < 6: return UseAbility(15995)
            if s3 and s3 < 6: return UseAbility(15992)
            if sr and sr < 6: return UseAbility(15991)
        else:
            if s3 and s3 < 6: return UseAbility(15992)
            if cnt1 and a3 and a3 < 6: return UseAbility(15996)
            if sr and sr < 6: return UseAbility(15991)
            if cnt1 and ar and ar < 6: return UseAbility(15995)

        if not data[15997] and data[15998] > 5 and cnt1 < 4 and res:
            return UseAbility(15997)  # 如果不会耽误大舞

        if res and data.gauge.esprit >= 50 and 1822 in data.effects:
            return UseAbility(16005)  # 大舞内交剑舞

        if res:
            if cnt1 > 1:  # 触发技能使用
                if a3: return UseAbility(15996)
                if ar: return UseAbility(15995)
                if s3: return UseAbility(15992)
                if sr: return UseAbility(15991)
            else:
                if s3: return UseAbility(15992)
                if cnt1 and a3: return UseAbility(15996)
                if sr and sr < 6: return UseAbility(15991)
                if cnt1 and ar: return UseAbility(15995)

        if data.combo_id == 15989 and data.me.level >= 2:
            return UseAbility(15990)
        elif data.combo_id == 15993 and cnt1 and data.me.level >= 25:
            return UseAbility(15994)
        else:
            return UseAbility(15993 if cnt1 > 1 and data.me.level > 15 else 15989)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if data.config.query_ability:
            return data.config.get_query_ability()
        if 1818 in data.effects or 1819 in data.effects or data.target_distance > 25: return
        res = res_lv(data)
        if res:
            if data[15998] > 100 and not data[16011]:
                return UseAbility(16011)
            if data[15998] > 40 and not data[16013] and not {1815, 1814, 1817, 1816}.intersection(set(data.effects.keys())):
                return UseAbility(16013)
        if 1820 in data.effects and (res or data.effects[1820].timer < 3):
            return UseAbility(16009)
        if self.last_feather < perf_counter() - 1.5 and (data.gauge.feathers >= 1 and res and 1822 in data.effects or data.gauge.feathers >= 4):
            self.last_feather = perf_counter()
            return UseAbility(16008 if count_enemy(data, 1) > 1 and data.me.level >= 50 else 16007)
