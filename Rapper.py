from FFxivPythonTrigger import PluginBase, hook, api
from ctypes import *

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_pattern

sig_main = "48 89 5C 24 ? 57 48 83 EC ? 48 8B F9 0F 29 74 24 ? 0F B6 49 ?"
command = '@rap'


class Rapper(PluginBase):
    name = "Rapper"

    def __init__(self):
        super().__init__()

        class SwingHook(hook.Hook):
            argtypes = [c_uint64, c_int, c_float]
            restype = c_uint64

            def hook_function(_self, base, action_id, time):
                return _self.original(base, action_id, time - self.reduce)

        self.reduce = 0
        self.swing_hook = SwingHook(AddressManager(self.storage.data, self.logger).get('swing_set', scan_pattern, sig_main))
        self.storage.save()
        api.command.register(command, self.process_command)

    def _start(self):
        self.swing_hook.install()
        self.swing_hook.enable()

    def _onunload(self):
        self.swing_hook.uninstall()

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
