from FFxivPythonTrigger import PluginBase, hook, api
from ctypes import *

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_pattern, write_float

sig_set = "48 89 5C 24 ? 57 48 83 EC ? 48 8B F9 0F 29 74 24 ? 0F B6 49 ?"
sig_read = "40 53 57 41 56 41 57 48 83 EC ? 4C 8B 35 ? ? ? ?"
sig_base = "41 C7 45 ? ? ? ? ? 49 8B 07 FF 90 ? ? ? ?"
command = '@rap'


class Rapper(PluginBase):
    name = "Rapper"

    def __init__(self):
        super().__init__()

        class SwingReadHook(hook.Hook):
            argtypes = [c_uint, c_int64, c_uint, c_int64]
            restype = c_int

            def hook_function(_self, *args):
                return max(int(_self.original(*args) - self.reduce * 1000), 0)

        class SwingSetHook(hook.Hook):
            argtypes = [c_uint64, c_int, c_float]
            restype = c_uint64

            def hook_function(_self, base, action_id, time):
                return _self.original(base, action_id, time - self.reduce)

        self.reduce = 0
        am = AddressManager(self.storage.data, self.logger)
        self.swing_set_hook = SwingSetHook(am.get('swing_set', scan_pattern, sig_set))
        self.swing_read_hook = SwingReadHook(am.get('swing_read', scan_pattern, sig_read))
        self.addr_base = am.get('swing_base', scan_pattern, sig_base) + 4
        self.storage.save()
        api.command.register(command, self.process_command)

    def _start(self):
        self.swing_set_hook.install()
        self.swing_read_hook.install()
        self.swing_set_hook.enable()
        self.swing_read_hook.enable()
        write_float(self.addr_base, self.reduce)

    def _onunload(self):
        self.swing_set_hook.uninstall()
        self.swing_read_hook.uninstall()
        write_float(self.addr_base, 0)
        api.command.unregister(command)

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if arg[0] == "set":
                self.reduce = float(arg[1])
                write_float(self.addr_base, self.reduce)
                return "set to %s" % self.reduce
            elif arg[0] == "get":
                return self.reduce
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            return str(e)
