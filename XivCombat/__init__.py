from ctypes import *

from FFxivPythonTrigger import PluginBase, api, frame_inject, SaintCoinach
# from Lumina.Excel.GeneratedSheets import Action
from traceback import format_exc
from time import perf_counter

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.AttrContainer import AttributeNotFoundException
from FFxivPythonTrigger.Logger import debug
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_pattern
from . import LogicData

# action_sheet = lumina.lumina.GetExcelSheet[Action]()
action_sheet = SaintCoinach.realm.game_data.get_sheet('Action')
command = "@aCombat"

fight_strategies = dict()
common_strategies = dict()
is_area_action_cache = dict()

from . import Machinist, Gunbreaker, DarkKnight, Warrior, Dancer, Summoner, Paladin, Bard

fight_strategies |= Machinist.fight_strategies
fight_strategies |= Gunbreaker.fight_strategies
fight_strategies |= DarkKnight.fight_strategies
fight_strategies |= Warrior.fight_strategies
fight_strategies |= Dancer.fight_strategies
fight_strategies |= Summoner.fight_strategies
fight_strategies |= Paladin.fight_strategies
fight_strategies |= Bard.fight_strategies

common_strategies |= Dancer.common_strategies


class ContinueException(Exception):
    pass


def get_me():
    return api.XivMemory.actor_table.get_me()


def get_target():
    return api.XivMemory.targets.current


def get_mo_target():
    try:
        return api.MoPlus.entity
    except AttributeNotFoundException:
        return api.XivMemory.targets.mouse_over


def use_skill(action_id, target_id=0xe0000000):
    # debug("t",action_id)
    if action_id not in is_area_action_cache:
        is_area_action_cache[action_id] = action_sheet[action_id]['TargetArea']
    if is_area_action_cache[action_id]:
        actor = api.XivMemory.actor_table.get_actor_by_id(target_id) if target_id != 0xe0000000 else get_me()
        if actor is not None:
            api.Magic.do_action.do_action_location(1, action_id, actor.pos.x, actor.pos.y, actor.pos.z, actor.id)
    else:
        api.XivMemory.combat_data.skill_queue.use_skill(action_id, target_id)


class XivCombat(PluginBase):
    name = "xiv combat"

    def __init__(self):
        super().__init__()

        class ForceActionHook(Hook):
            restype = c_int64
            argtypes = [c_int64, c_uint, c_uint, c_int64, c_uint, c_uint, c_int]

            def hook_function(_self, action_manager_addr, action_type, action_id, target_id, unk1, unk2, unk3):
                original = self.state['use']
                self.state['use'] = False
                if self.is_processing and self.work:
                    if action_type == 1:
                        use_skill(action_id, target_id)
                    elif action_type == 2 or action_type == 5:
                        api.XivMemory.combat_data.skill_ani_lock = 0
                a = _self.original(action_manager_addr, action_type, action_id, target_id, unk1, unk2, unk3)
                self.state['use'] = original
                return a

        self.force_action_hook = ForceActionHook(
            AddressManager(self.storage.data, self.logger)
                .get('do_action', scan_pattern, "40 53 55 57 41 54 41 57 48 83 EC ? 83 BC 24 ? ? ? ? ?")
        )
        self.storage.save()

        self.state = self.storage.data.setdefault('config', dict())
        self.state.setdefault('use', False)
        self.state.setdefault('single', True)
        self.state.setdefault('violent', True)
        self.state.setdefault('find', False)
        self.work = False
        self.is_processing = False

        self.nAbility = [None, 0]
        self.nSkill = [None, 0]
        api.command.register(command, self.process_command)
        self.register_event("network/action_effect", self.deal_network_action)
        frame_inject.register_continue_call(self.action)
        self.next_work_time = 0
        self.count_error = 0

        api.Magic.echo_msg(self.get_status_string())

    def deal_network_action(self, evt):
        if evt.source_id != api.XivMemory.actor_table.get_me().id or evt.action_type != 'action':
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

    def _onunload(self):
        self.work = False
        api.command.unregister(command)
        frame_inject.unregister_continue_call(self.action)
        self.force_action_hook.uninstall()

    def action(self):
        if self.work and perf_counter() > self.next_work_time and not api.XivMemory.combat_data.skill_queue.mark1:
            next_period = 0.1
            try:
                if self.state['use']:
                    try:
                        round_data = LogicData.LogicData(self.state, self.nSkill[0], self.nAbility[0])
                    except LogicData.NoMeActorException:
                        next_period = 0.5
                        self.is_processing = False
                        raise ContinueException()
                    except LogicData.ActorDeadException:
                        self.is_processing = False
                        raise ContinueException()
                    except LogicData.TargetNotExistsException:
                        self.is_processing = False
                    except LogicData.TargetIsSelfException:
                        self.is_processing = False
                    except LogicData.NoValidEnemyException:
                        self.is_processing = False
                        raise ContinueException()
                    else:
                        if not (round_data.me.CastingID):
                            ans = None
                            if round_data.job in common_strategies:
                                ans = common_strategies[round_data.job](round_data)
                            if (ans is None) and api.XivMemory.combat_data.is_in_fight and (round_data.job in fight_strategies):
                                ans = fight_strategies[round_data.job](round_data)
                            if ans is not None:
                                self.is_processing = True
                                action, target = ans if type(ans) == tuple else (ans, round_data.target.id)
                                if (action, target) == self.nSkill[0]:
                                    self.nSkill = [None, 0]
                                elif (action, target) == self.nAbility[0]:
                                    self.nAbility = [None, 0]
                                use_skill(action, target)
                                next_period = 0.4
                                raise ContinueException()
                        self.is_processing = False
                else:
                    self.is_processing = False
                if self.nSkill[0] is not None and api.XivMemory.combat_data.cool_down_group.gcd_group.remain < 0.2:
                    use_skill(*self.nSkill[0])
                    self.nSkill = [None, 0]
                elif self.nAbility[0] is not None:
                    use_skill(*self.nAbility[0])
                    self.nAbility = [None, 0]
            except ContinueException:
                self.count_error = 0
            except Exception:
                self.logger.error("error occurred:\n" + format_exc())
                self.count_error += 1
                if self.count_error >= 20:
                    self.logger.error("end because too many error occurred")
                    self.work = False
            else:
                self.count_error = 0
            self.next_work_time = perf_counter() + next_period

    def _start(self):
        self.work = True
        self.force_action_hook.install()
        self.force_action_hook.enable()

    def get_status_string(self):
        s = "[active]" if self.state['use'] else "[inactive]"
        s += "[single]" if self.state['single'] else "[multi]"
        if self.state['violent']: s += " [violent]"
        if self.state['find']: s += " [find]"
        return s

    def queue_skill_command(self, args):
        sid = int(args[1])
        force = False
        is_skill = None
        if args[0] == "s":
            is_skill = True
        elif args[0] == "a":
            is_skill = False
        elif args[0] == "f":
            force = True
        else:
            return "unknown args: %s" % args[0]
        try:
            if len(args) > 2:
                if args[2] == "t":
                    target = get_target()
                elif args[2] == "mo":
                    target = get_mo_target()
                elif args[2] == "me":
                    target = get_me()
                else:
                    return "unknown args: %s" % args[2]
            else:
                target = get_target()
            target = target if target is not None else get_me()
        except Exception:
            target = get_me()
        tid = target.id
        temp = (sid, tid)
        if force:
            self.force_use_skill(*temp)
            return "force - name: {} / target: {}".format(self.get_action_name(sid), target.decoded_name)
        else:
            t = self.nSkill if is_skill else self.nAbility
            if temp == t[0]:
                t[1] += 1
                if t[1] >= 3:
                    self.force_use_skill(*temp)
                    t[0] = None
                    t[1] = 0
                    return "force - name: {} / target: {}".format(self.get_action_name(sid), target.decoded_name)
            else:
                t[0] = temp
                t[1] = 0
        return "next {} - name: {} / target: {}".format("skill" if is_skill else "ability", self.get_action_name(sid), target.decoded_name)

    def get_action_name(self, action_id):
        return action_sheet[action_id]['Name']

    def process_command(self, args):
        if args[0] == "q":
            msg = self.queue_skill_command(args[1:])
            if msg is not None:
                api.Magic.echo_msg(msg)
            return
        elif args[0] == "off":
            self.state['use'] = False
        elif args[0] == "on":
            self.state['use'] = True
            if len(args) > 1:
                if args[1] == "s":
                    self.state['single'] = True
                elif args[1] == "m":
                    self.state['single'] = False
                else:
                    api.Magic.echo_msg("unknown args: %s" % args[1])
        elif args[0] == "violent":
            if len(args) > 1:
                if args[1] == "on":
                    self.state['violent'] = True
                elif args[1] == "off":
                    self.state['violent'] = False
                else:
                    api.Magic.echo_msg("unknown args: %s" % args[1])
            else:
                self.state['violent'] = not self.state['violent']
        elif args[0] == "find":
            if len(args) > 1:
                if args[1] == "on":
                    self.state['find'] = True
                elif args[1] == "off":
                    self.state['find'] = False
                else:
                    api.Magic.echo_msg("unknown args: %s" % args[1])
            else:
                self.state['find'] = not self.state['find']
        else:
            api.Magic.echo_msg("unknown args: %s" % args[0])
        self.storage.save()
        api.Magic.echo_msg(self.get_status_string())

    def force_use_skill(self, action_id, target_id=0xe0000000):
        original = self.state['use']
        self.state['use'] = False
        api.XivMemory.combat_data.skill_ani_lock = 0
        use_skill(action_id, target_id)
        self.state['use'] = original
