from FFxivPythonTrigger import PluginBase, hook, api
from ctypes import *

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_pattern

sig_main = "48 83 EC ?? 80 B9 04 01 00 00 ?? 74"
sig_fly = "40 ?? 48 83 EC ?? 48 8B ?? 48 8B ?? FF 90 ?? ?? ?? ?? 48 85 ?? 75"
command = '@speedH'


class SpeedHookMain(hook.Hook):
    restype = c_float
    argtypes = [c_int64, c_byte, c_int]

    def __init__(self, func_address: int):
        super(SpeedHookMain, self).__init__(func_address)
        self.percent = 1

    def hook_function(self, a1, a2, a3):
        return self.original(a1, a2, a3) * self.percent


class SpeedHookFly(hook.Hook):
    restype = c_float
    argtypes = [c_void_p]

    def __init__(self, func_address: int):
        super(SpeedHookFly, self).__init__(func_address)
        self.percent = 1

    def hook_function(self, a1):
        return self.original(a1) * self.percent

class SpeedHack(PluginBase):
    name = "speed hack"

    def __init__(self):
        super().__init__()
        am=AddressManager(self.storage.data, self.logger)
        addrMain = am.get('main',scan_pattern,sig_main)
        addrFly = am.get('fly',scan_pattern,sig_fly)
        self.storage.save()
        self.hook_main = SpeedHookMain(addrMain)
        self.hook_fly = SpeedHookFly(addrFly)
        api.command.register(command, self.process_command)

    def _start(self):
        self.hook_main.install()
        self.hook_fly.install()
        self.hook_main.enable()
        self.hook_fly.enable()

    def _onunload(self):
        self.hook_main.uninstall()
        self.hook_fly.uninstall()

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if arg[0] == "set":
                self.hook_main.percent = float(arg[1])
                self.hook_fly.percent = float(arg[1])
                return "set to %s" % arg[1]
            elif arg[0] == "get":
                return self.hook_main.percent
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            return str(e)
