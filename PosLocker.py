from FFxivPythonTrigger import *
from ctypes import *

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_address, read_memory,scan_pattern
from FFxivPythonTrigger.memory.StructFactory import PointerStruct

command = "@posL"
pattern_main = "f3 0f ?? ?? ?? ?? ?? ?? eb ?? 48 8b ?? ?? ?? ?? ?? e8 ?? ?? ?? ?? 48 85"
pattern_actor_move = "40 53 48 83 EC ? F3 0F 11 89 ? ? ? ? 48 8B D9 F3 0F 11 91 ? ? ? ?"


class PosLocker(PluginBase):
    name = "PosLocker"

    def __init__(self):
        super().__init__()
        self.statements = set()

        am = AddressManager(self.storage.data, self.logger)
        ptr_main = am.get("main ptr", scan_address, pattern_main, add=0x14, cmd_len=8)
        addr_move_func = am.get("move func addr", scan_pattern, pattern_actor_move)
        self.storage.save()

        self.main_addr = cast(ptr_main,POINTER(c_int64))
        self.main_coor = read_memory(PointerStruct(c_float * 3, 160), ptr_main)
        self._enable = False

        class ActorMoveHook(Hook):
            restype = c_int64
            argtypes = [c_int64, c_float, c_float, c_float]

            def hook_function(_self, addr, x, z, y):
                if self.main_addr[0] == addr and (self._enable or self.get_result()):
                    return _self.original(addr, *self.main_coor.value)
                return _self.original(addr, x, z, y)

        self.hook = ActorMoveHook(addr_move_func)
        api.command.register(command, self.process_command)
        self.register_api('PosLock', type('obj', (object,), {
            'enable': self.enable,
            'disable': self.disable,
            'register_statement': self.register_statement,
            'remove_statement': self.remove_statement,
        }))

    def process_command(self, args):
        if args:
            if args[0] == 'on':
                self._enable = True
            elif args[0] == 'off':
                self._enable = False
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            self._enable = not self._enable
        api.Magic.echo_msg("pl: [%s]" % ('enable' if self._enable else 'disable'))

    def _start(self):
        self.hook.enable()

    def _onunload(self):
        api.command.unregister(command)
        self.hook.uninstall()

    def get_result(self):
        for statement in self.statements:
            if statement():
                return True
        return False

    def enable(self):
        self._enable = True

    def disable(self):
        self._enable = False

    def register_statement(self, statement):
        self.statements.add(statement)

    def remove_statement(self, statement):
        try:
            self.statements.remove(statement)
            return True
        except KeyError:
            return False
