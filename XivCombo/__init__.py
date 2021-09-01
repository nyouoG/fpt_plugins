import os
from importlib import import_module
from pathlib import Path

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger import PluginBase
from FFxivPythonTrigger import api
from ctypes import *
from traceback import format_exc

from FFxivPythonTrigger.memory import scan_pattern

command = "@combo"

# get_icon_sig = "48 89 ? ? ? 48 89 ? ? ? 48 89 ? ? ? 57 48 83 EC ? 8B DA BE" #cn.5.35
get_icon_sig = "48 89 ? ? ? 48 89 ? ? ? 57 48 83 EC ? 8B DA BE"  # cn.5.40
is_icon_replaceable_sig = "81 F9 ?? ?? ?? ?? 7F 39 81 F9 ?? ?? ?? ??"


class XivCombo(PluginBase):
    name = "xiv combo"
    git_repo = 'nyouoG/fpt_plugins'
    repo_path = 'XivCombo'
    hash_path = os.path.dirname(__file__)

    def __init__(self):
        super().__init__()

        class OnGetIconHook(self.PluginHook):
            restype = c_ulonglong
            argtypes = [c_ubyte, c_uint]

            def hook_function(_self, a1, action_id):
                if action_id in self.enable_combos:
                    try:
                        me = api.XivMemory.actor_table.get_me()
                        if me is not None:
                            return _self.original(a1, self.enable_combos[action_id](me))
                    except Exception:
                        self.logger.error("error occured:\n" + format_exc())
                return _self.original(a1, action_id)

        class OnCheckIsIconReplaceableHook(self.PluginHook):
            restype = c_ulonglong
            argtypes = [c_uint]

            def hook_function(self, action_id):
                return int((action_id in self.enable_combos) or (self.original(action_id)))

        self.all_combos = dict()
        for f in (Path(__file__).parent / 'Combos').glob('*.py'):
            if f.stem == '__init__': continue
            module = import_module(f'.Combos.{f.stem}', __name__)
            if hasattr(module, 'combos') and isinstance(module.combos, dict):
                self.all_combos |= module.combos
                self.logger.debug(f"loaded combos from .Combos.{f.stem}")

        am = AddressManager(self.storage.data, self.logger)
        get_icon_addr = am.get("get icon", scan_pattern, get_icon_sig)
        is_icon_replaceable_addr = am.get("is icon replaceable", scan_pattern, is_icon_replaceable_sig)
        self.enable_combos = dict()
        self.enable_combos_name = dict()
        self.on_get_icon_hook = OnGetIconHook(get_icon_addr, True)
        self.on_is_icon_replaceable_hook = OnCheckIsIconReplaceableHook(is_icon_replaceable_addr, True)
        self.load_combo()
        self.storage.save()

        api.command.register(command, self.process_command)

    def load_combo(self):
        temp = dict()
        temp_name = dict()
        data = self.storage.data.setdefault('enabled', dict())
        for key in self.all_combos.keys():
            if data.setdefault(key, False):
                action_id, function = self.all_combos[key]
                if action_id in temp:
                    self.logger.error(f"a combo with id:{action_id} name:{temp_name[action_id]} is already enabled, {key} will be disabled")
                    data[key] = False
                else:
                    temp[action_id] = function
                    temp_name[action_id] = key
        self.enable_combos = temp
        self.enable_combos_name = temp_name

    def _onunload(self):
        api.command.unregister(command)

    def process_command(self, args):
        try:
            ans = self._process_command(args)
            if ans is not None:
                api.Magic.echo_msg(ans)
            self.storage.save()
        except Exception as e:
            self.logger.error(format_exc())
            api.Magic.echo_msg(e)

    def _process_command(self, args):
        if not args:
            return f"format: /e {command} [combo_key] [enable / disable / e / d]"
        if len(args) != 2:
            return "invalid argument length"
        key, status_str = args
        if key not in self.all_combos:
            return f"[{key}] is an unregistered combo key"
        action_id, function = self.all_combos[key]
        if status_str == "enable" or status_str == "e":
            status = True
        elif status_str == "disable" or status_str == "d":
            status = False
        else:
            return f"unknown args 2: [{status_str}]"
        data = self.storage.data.setdefault('enabled', dict())
        if status == data.setdefault(key, False):
            return f"[{key}] is already " + ("enabled" if status else "disabled")
        if status and action_id in self.enable_combos:
            return f"a combo with same id:{action_id} name:{self.enable_combos_name[action_id]} is already enabled"
        data[key] = status
        self.load_combo()
        return f"[{key}] " + ("enabled" if status else "disabled")
