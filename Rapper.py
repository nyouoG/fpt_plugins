from FFxivPythonTrigger import PluginBase, api
from ctypes import *

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_pattern

sig_sync = "F6 05 ? ? ? ? ? 74 ? 0F 2F 05 ? ? ? ?"
sig_read = "40 53 57 41 56 41 57 48 83 EC ? 4C 8B 35 ? ? ? ?"
command = '@rap'


class Rapper(PluginBase):
    name = "Rapper"

    def __init__(self):
        super().__init__()

        class SwingReadHook(self.PluginHook):
            argtypes = [c_uint, c_int64, c_uint, c_int64]
            restype = c_int

            def hook_function(_self, *args):
                return max(int(_self.original(*args) - self.reduce * 1000), 0)

        class SwingSyncHook(self.PluginHook):
            argtypes = [c_float]
            restype = c_float

            def hook_function(_self, *args):
                return max(_self.original(*args) - self.reduce, 0.)

        self.reduce = 0
        am = AddressManager(self.storage.data, self.logger)
        self.swing_sync_hook = SwingSyncHook(am.get('swing_sync', scan_pattern, sig_sync), True)
        self.swing_read_hook = SwingReadHook(am.get('swing_read', scan_pattern, sig_read), True)
        self.storage.save()
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if arg[0] == "set":
                self.reduce = float(arg[1])
                return "set to %s" % self.reduce
            elif arg[0] == "get":
                return self.reduce
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            return str(e)
