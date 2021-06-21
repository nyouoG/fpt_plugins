####################
# enable 是否启用 bool
####################
# resource 资源策略 int
# -1 : 保存资源，最低限度输出
# 0 : 自动判断，基于目标ttk
# 1 : 正常循环
# 2 : 资源爆发
####################
# single 单体群体策略 int
# -1 : 强制群体
# 0 : 自动判断，基于敌人列表
# 1 : 强制单体
####################
# target 选取目标策略（优先级） list[str]
# current : 当前目标
# focus : 焦点目标
# list_distance : 敌人列表中最近的目标
# list_hp : 敌人列表中绝对血量最低的目标
# list_hpp : 敌人列表中血量百分比最低的目标
####################
# pairing 职业配对策略 dict[Union[str, int],str]
# key : 职业id、名称
# value : 策略模块名
####################

from importlib import reload, import_module
from inspect import isclass
from threading import Lock
from typing import Union, Optional, Callable, Tuple, Type

from .Strategy import Strategy, UseAbility, UseItem, UseCommon


class ConfigError(Exception):
    pass


class CombatConfig(object):
    query_skill: Optional[Union[UseAbility, UseItem, UseCommon]]
    query_ability: Optional[Union[UseAbility, UseItem, UseCommon]]
    _pairing: dict[Union[str, int], Optional[Strategy]]

    def __init__(self,
                 enable: bool = False,
                 resource: int = 0,
                 single: int = 0,
                 target: list[str] = None,
                 pairing: dict[Union[str, int], str] = None,
                 custom_settings: dict[str, any] = None,
                 enable_extra_enemies=False,
                 extra_enemies_combat_only=True,
                 extra_enemies_distance: int = 15,
                 ):
        self.enable = enable
        self.resource = resource
        self.single = single
        self.pairing = pairing if pairing is not None else dict()
        self._pairing = dict()
        self.pair_lock = Lock()
        self.target = target if target is not None else []
        self.custom_settings: dict[str, any] = custom_settings if custom_settings is not None else dict()
        self.enable_extra_enemies = enable_extra_enemies
        self.extra_enemies_combat_only = extra_enemies_combat_only
        self.extra_enemies_distance = extra_enemies_distance

        # some data for processing
        self.ability_cnt = 0
        self.next_work_time = -1
        self.err_count = 0
        self.query_skill = None
        self.query_ability = None
        self.skill_disable: set[int] = set()

    def get_query_ability(self):
        temp = self.query_ability
        self.query_ability = None
        return temp

    def get_query_skill(self):
        temp = self.query_skill
        self.query_skill = None
        return temp

    def get_dict(self):
        return {
            'enable': self.enable,
            'resource': self.resource,
            'single': self.single,
            'pairing': self.pairing,
            'target': self.target,
            'custom_settings': self.custom_settings,
            'enable_extra_enemies': self.enable_extra_enemies,
            'extra_enemies_combat_only': self.extra_enemies_combat_only,
            'extra_enemies_distance': self.extra_enemies_distance,
        }

    def load_logic(self, module_name: str):
        try:
            module = import_module(f"..Strategies.{module_name}", package=__name__)
        except ImportError as e:
            raise ConfigError(f"[{module_name}] cant be imported: {e}")
        module = reload(module)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isclass(attr) and issubclass(attr, Strategy) and attr != Strategy:
                return attr(self)
        raise ConfigError(f"[{module_name}] do not have a valid strategy")

    def get_strategy(self, job_class_id: Union[str, int]) -> Optional[Strategy]:
        if job_class_id not in self._pairing:
            if not self.pair_lock.acquire(False):
                return None
            if job_class_id not in self.pairing:
                self._pairing[job_class_id] = None
            else:
                try:
                    self._pairing[job_class_id] = self.load_logic(self.pairing[job_class_id])
                except Exception:
                    self._pairing[job_class_id] = None
                    self.pair_lock.release()
                    raise
            self.pair_lock.release()
        return self._pairing[job_class_id]

    def set_strategy(self, job_class_id: Union[str, int], module_name: Optional[str]) -> Optional[Strategy]:
        with self.pair_lock:
            if job_class_id in self._pairing:
                del self._pairing[job_class_id]

            if module_name is None:
                self._pairing[job_class_id] = None
                try:
                    del self.pairing[job_class_id]
                except KeyError:
                    pass
            else:
                self._pairing[job_class_id] = self.load_logic(module_name)
                self.pairing[job_class_id] = module_name
        return self._pairing[job_class_id]
