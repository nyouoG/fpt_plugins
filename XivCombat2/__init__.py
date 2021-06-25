from ctypes import *
from threading import Lock
from time import perf_counter, sleep
from traceback import format_exc

from FFxivPythonTrigger import PluginBase, frame_inject, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_pattern
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

from . import Config, Api, LogicData, Strategy, Define

ERR_LIMIT = 20
DEFAULT_PERIOD = 0.2
command = "@aCombat"
action_sheet = realm.game_data.get_sheet('Action')
is_area_action_cache = dict()


def target_key(key: str):
    if key == "[t]":
        t = Api.get_current_target()
    elif key == "[me]":
        t = Api.get_me_actor()
    elif key == "[f]":
        t = Api.get_focus_target()
    elif key == "[mo]":
        t = Api.get_mo_target()
    else:
        return key
    return t.id if t is not None else Api.get_me_actor().id


def use_item(to_use: Strategy.UseItem):
    Api.reset_ani_lock()  # 因为有动画锁就会卡掉do_action，所以需要直接清除（请注意使用频率）
    if to_use.priority == Define.HQ_ONLY:  # 后面改select、case吧
        if Api.get_backpack_item_count(to_use.item_id, is_hq=True):
            Api.use_item(to_use.item_id, True, to_use.target_id)
    elif to_use.priority == Define.NQ_ONLY:
        if Api.get_backpack_item_count(to_use.item_id, is_hq=False):
            Api.use_item(to_use.item_id, False, to_use.target_id)
    elif to_use.priority == Define.HQ_FIRST:
        if Api.get_backpack_item_count(to_use.item_id, is_hq=True):
            Api.use_item(to_use.item_id, True, to_use.target_id)
        elif Api.get_backpack_item_count(to_use.item_id, is_hq=False):
            Api.use_item(to_use.item_id, False, to_use.target_id)
    elif to_use.priority == Define.NQ_FIRST:
        if Api.get_backpack_item_count(to_use.item_id, is_hq=False):
            Api.use_item(to_use.item_id, False, to_use.target_id)
        elif Api.get_backpack_item_count(to_use.item_id, is_hq=True):
            Api.use_item(to_use.item_id, True, to_use.target_id)


def use_ability(to_use: Strategy.UseAbility):
    if to_use.ability_id is None: return
    if to_use.ability_id not in is_area_action_cache:
        is_area_action_cache[to_use.ability_id] = action_sheet[to_use.ability_id]['TargetArea']
    if is_area_action_cache[to_use.ability_id]:
        actor = Api.get_actor_by_id(to_use.target_id) if to_use.target_id != 0xe0000000 else Api.get_me_actor()
        if actor is not None:
            Api.use_area_action(to_use.ability_id, actor.pos.x, actor.pos.y, actor.pos.z, actor.id)
    else:
        Api.use_action(to_use.ability_id, to_use.target_id)


HotbarBlock = OffsetStruct({
    'type': (c_ubyte, 199),
    'param': (c_uint, 184),
})


class XivCombat2(PluginBase):
    name = "XivCombat2"

    def __init__(self):
        super().__init__()

        class HotbarProcessHook(Hook):
            restype = c_ubyte
            argtypes = [c_int64, POINTER(HotbarBlock)]

            def hook_function(_self, a1, block_p):
                try:
                    # self.logger(block_p[0].type, block_p[0].param,self.is_working , self.config.enable)
                    if not (self.is_working and self.config.enable):
                        return _self.original(a1, block_p)
                    block = block_p[0]
                    t = Api.get_current_target()
                    t_id = Api.get_me_actor().id if t is None else t.id
                    if block.type == 1:
                        self.config.enable = False
                        self.logger.debug(f"force action {block.param}")
                        self.config.ability_cnt += 1
                        use_ability(Strategy.UseAbility(block.param, t_id))
                        self.config.enable = True
                        return 1
                    elif block.type == 2 or block.type == 10:
                        self.config.enable = False
                        self.logger.debug(f"force {'item' if block.type == 2 else 'common'} {block.param}")
                        Api.reset_ani_lock()
                        Api.do_action(2 if block.type == 2 else 5, block.param, t_id)
                        self.config.enable = True
                        return 1
                except Exception:
                    self.logger.error("error in hotbar hook", format_exc())
                return _self.original(a1, block_p)

        self.config = Config.CombatConfig(
            **self.storage.data.setdefault('config', {
                'target': ["focus", "current", "list_distance"],
            })
        )
        self.hotbar_process_hook = HotbarProcessHook(
            AddressManager(self.storage.data, self.logger)
                .get('hotbar_process', scan_pattern, "48 89 5C 24 ? 48 89 6C 24 ? 48 89 74 24 ? 57 48 83 EC ? 0F B6 82 ? ? ? ?")
        )
        self.save_config()

        self.work = False
        self.is_working = False
        self.work_lock = Lock()
        api.command.register(command, self.process_command)
        self.register_event("network/action_effect", self.deal_network_action)

        # frame_inject.register_continue_call(self.process)

    def _onunload(self):
        api.command.unregister(command)
        self.hotbar_process_hook.uninstall()
        self.work = False
        self.main_mission.join(timeout=2)
        # frame_inject.unregister_continue_call(self.process)

    def _start(self):
        self.logger(self.config.get_dict())
        self.hotbar_process_hook.install()
        self.hotbar_process_hook.enable()
        self.work = True
        while self.work:  # 独立线程版本
            try:
                sleep_time = self._process() if self.config.enable else DEFAULT_PERIOD
            except Exception:
                self.logger.warning('error occurred while processing:\n', format_exc())
                self.config.err_count += 1
                if self.config.err_count > ERR_LIMIT:
                    self.logger.error('unregister process because of to many error occurred!')
                    self.work = False
                    break
                sleep_time = 0.5
            else:
                self.config.err_count = 0
            sleep(sleep_time)
        self.work = False

    def process(self):  # 帧逻辑版本
        if self.config.enable and perf_counter() > self.config.next_work_time:
            try:
                self.config.next_work_time = perf_counter() + self._process() + 0.01
            except Exception:
                self.logger.warning('error occurred while processing:\n', format_exc())
                self.config.err_count += 1
                if self.config.err_count > ERR_LIMIT:
                    self.logger.error('unregister process because of to many error occurred!')
                    frame_inject.unregister_continue_call(self.process)
                self.config.next_work_time = perf_counter() + 0.5
            else:
                self.config.err_count = 0

    def save_config(self):
        self.storage.data['config'] = self.config.get_dict()
        self.storage.save()

    def _process(self) -> float:
        # 判断是否执行
        data = LogicData.LogicData(self.config)
        if data.me is None or not data.me.currentHP: return 0.5  # 不存在角色、角色已经死亡
        if data.me.CastingTime - data.me.CastingProgress > 0.2: return DEFAULT_PERIOD  # 正在咏唱
        if not Api.skill_queue_is_empty(): return max(Api.get_ani_lock(), DEFAULT_PERIOD)  # 队列中存在技能

        # 获取决策行为
        to_use = None
        if data.gcd < 0.2: self.config.ability_cnt = 0
        process_non_gcd = data.gcd > 0.9 and self.config.ability_cnt < int(data.gcd_total) or data.gcd == 0
        strategy = self.config.get_strategy(data.job)
        if strategy is not None and (not strategy.fight_only or data.valid_enemies):
            self.is_working = True
            to_use = strategy.common(data)
            if to_use is None:
                if data.gcd < 0.2:
                    to_use = strategy.global_cool_down_ability(data)
                if to_use is None and process_non_gcd:
                    to_use = strategy.non_global_cool_down_ability(data)
                    if to_use is not None: self.config.ability_cnt += 1
        else:
            self.is_working = False
        if to_use is None:
            if data.gcd < 0.2:
                to_use = self.config.get_query_skill()
            if to_use is None:
                if process_non_gcd:
                    to_use = self.config.get_query_ability()
                    if to_use is not None: self.config.ability_cnt += 1
                if to_use is None: return DEFAULT_PERIOD

        # 处理决策行为
        if self.config.enable:
            if to_use.target_id is None:
                target = data.target
                to_use.target_id = data.me.id if target is None else target.id
            if Api.get_current_target() is None:
                Api.set_current_target(Api.get_actor_by_id(to_use.target_id))
            if isinstance(to_use, Strategy.UseAbility) and Api.skill_queue_is_empty():
                # actor=Api.get_actor_by_id(to_use.target_id)
                # self.logger.debug(f"use:{action_sheet[to_use.ability_id]['Name']} on {actor.Name}({hex(actor.id)[2:]}/{bin(actor.unitStatus1)}/{bin(actor._uint_0x98)}")
                use_ability(to_use)
            elif isinstance(to_use, Strategy.UseItem):  # 使用道具，应该只有食物或者爆发药吧？
                use_item(to_use)
            elif isinstance(to_use, Strategy.UseCommon):  # 通用技能——特指疾跑
                Api.reset_ani_lock()  # 因为有动画锁就会卡掉do_action，所以需要直接清除（请注意使用频率）
                Api.use_common(to_use.ability_id, to_use.target_id)
            else:
                pass  # 理论上来说应该，或许，不会有其他类型的吧？或者策略返回的错误类型？有空加个raise？

        return DEFAULT_PERIOD

    def status_str(self):
        return str(self.config.get_dict())

    def deal_network_action(self, evt):
        if evt.source_id != Api.get_me_actor().id or evt.action_type != 'action':
            return
        for t_id, effects in evt.targets.items():
            if t_id < 0x40000000: continue
            is_invincible = False
            for effect in effects:
                if 'invincible' in effect.tags or ('ability' in effect.tags and effect.param == 0):
                    is_invincible = True
                    break
            if is_invincible and t_id not in LogicData.invincible_actor:
                self.logger.debug(f"{hex(t_id)} is add as an invincible actor")
                LogicData.invincible_actor.add(t_id)
            if not is_invincible and t_id in LogicData.invincible_actor:
                self.logger.debug(f"{hex(t_id)} is remove as an invincible actor")
                try:
                    LogicData.invincible_actor.remove(t_id)
                except KeyError:
                    pass

    def _process_command(self, args):
        if not args:
            return self.status_str()
        elif args[0] == "enable":
            self.config.enable = True
        elif args[0] == "disable":
            self.config.enable = False
        elif args[0] == "single":
            self.config.single = int(args[1])
        elif args[0] == "res":
            self.config.resource = int(args[1])
        elif args[0] == "load":
            if args[1] == "current":
                key = Api.get_current_job()
            else:
                try:
                    key = int(args[1])
                except ValueError:
                    key = args[1]
            return self.config.set_strategy(key, args[2])
        elif args[0] == "target":
            old = self.config.target.copy()
            self.config.target = args[1:]
            return f"{old} => {self.config.target}"
        elif args[0] == "query" or args[0] == "q":
            if len(args) < 4:
                t = Api.get_current_target()
                target = Api.get_me_actor().id if t is None else t.id
            else:
                target = int(target_key(args[3]))
            a = Strategy.UseAbility(int(args[2]), target)
            if args[1] == "ability" or args[1] == "a":
                self.config.query_ability = a
            elif args[1] == "skill" or args[1] == "s":
                self.config.query_skill = a
            elif args[1] == "force" or args[1] == "f":
                Api.reset_ani_lock()
                self.config.ability_cnt += 1
                use_ability(a)
            else:
                return f"unknown args: [{args[1]}]"
        elif args[0] == "skill_disable":
            s = int(args[1])
            if len(args < 3):
                if s in self.config.skill_disable:
                    try:
                        self.config.skill_disable.remove(s)
                    except KeyError:
                        pass
                    a = True
                else:
                    self.config.skill_disable.add(s)
                    a = False
            elif args[2] == "enable":
                try:
                    self.config.skill_disable.remove(s)
                except KeyError:
                    pass
                a = True
            elif args[2] == "disable":
                self.config.skill_disable.add(s)
                a = False
            else:
                return f"unknown args: [{args[2]}]"
            return f"{'enable' if a else 'disable'} {action_sheet[s]['Name']}"
        elif args[0] == "extra_enemies":
            if len(args) < 2:
                return f"enable:{self.config.enable_extra_enemies}, combat_only:{self.config.extra_enemies_combat_only}"
            elif args[1] == "enable":
                self.config.enable_extra_enemies = True
            elif args[1] == "disable":
                self.config.enable_extra_enemies = False
            elif args[1] == "combat_only":
                if len(args) < 3:
                    return self.config.extra_enemies_combat_only
                elif args[2] == "enable":
                    self.config.extra_enemies_combat_only = True
                elif args[2] == "disable":
                    self.config.extra_enemies_combat_only = False
                else:
                    return f"unknown args: [{args[2]}]"
            elif args[1] == "distance":
                if len(args) < 3:
                    return self.config.extra_enemies_distance
                else:
                    self.config.extra_enemies_distance = int(args[2])
            else:
                return f"unknown args: [{args[1]}]"
        elif args[0] == "set":
            self.config.custom_settings[args[1]] = ' '.join(args[2:])
            return self.config.custom_settings
        else:
            return f"unknown args: [{args[0]}]"

    def process_command(self, args):
        try:
            ans = self._process_command(args)
            if ans is not None:
                api.Magic.echo_msg(ans)
            self.save_config()
            # self.logger(self.config.get_dict())
        except Exception as e:
            self.logger.error(format_exc())
            api.Magic.echo_msg(e)
