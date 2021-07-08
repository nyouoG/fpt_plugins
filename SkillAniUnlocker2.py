from ctypes import *

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import read_memory, scan_pattern
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

command = "@sALock"
sig = "4C 89 44 24 ? 53 56 57 41 54 41 57"

a4_struct = OffsetStruct({
    'action_id': (c_ushort, 28),
    'action_id_2': (c_uint, 8),
    'time': (c_float, 16)
})

DEFAULT_LOCK_TIME = 0.6
DEFAULT_HACK_LOCK = 0.15


class SkillAniUnlocker2(PluginBase):
    name = "SkillAniUnlocker2"

    def __init__(self):
        super().__init__()

        class ActionHook(Hook):
            argtypes = [c_int, c_int64, c_int64, c_int64, c_int64, c_int64]
            restype = c_int64

            def hook_function(_self, a1, a2, a3, a4, a5, a6):
                if self.enable:
                    data = read_memory(a4_struct, a4)
                    if data.time > self.lock_time:
                        data.time = self.lock_time
                return _self.original(a1, a2, a3, a4, a5, a6)

        self.lock_time = DEFAULT_HACK_LOCK
        self.enable = False
        self.hook = ActionHook(AddressManager(self.storage.data, self.logger).get('addr', scan_pattern, sig))
        self.storage.save()
        api.command.register(command, self.process_command)

    def _start(self):
        self.hook.install()
        self.hook.enable()

    def _onunload(self):
        api.command.unregister(command, self.process_command)
        self.hook.uninstall()

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def status(self):
        return f"patch:{self.lock_time}" if self.enable else "dispatch"

    def _process_command(self, args):
        try:
            if len(args):
                if args[0] == "patch" or args[0] == "p":
                    self.enable = True
                    if len(args) > 1: self.lock_time = float(args[1])
                    else: self.lock_time = DEFAULT_HACK_LOCK
                elif args[0] == "dispatch" or args[0] == "d":
                    self.enable = False
                else:
                    return "unknown arguments {}".format(args[0])
            else:
                self.enable = not self.enable
            return self.status()
        except Exception as e:
            return str(e)
