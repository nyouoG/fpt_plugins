from FFxivPythonTrigger import PluginBase, api
from ctypes import *

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_pattern

sig_main = "48 83 EC ?? 80 B9 04 01 00 00 ?? 74"
sig_fly = "40 ?? 48 83 EC ?? 48 8B ?? 48 8B ?? FF 90 ?? ?? ?? ?? 48 85 ?? 75"
command = '@speedH'


class SpeedHack(PluginBase):
    name = "speed hack"
    git_repo = 'nyouoG/fpt_plugins'
    repo_path = 'SpeedHack.py'
    hash_path = __file__

    def __init__(self):
        super().__init__()

        class SpeedHookMain(self.PluginHook):
            restype = c_float
            argtypes = [c_int64, c_byte, c_int]

            def hook_function(_self, a1, a2, a3):
                return _self.original(a1, a2, a3) * self.percent

        class SpeedHookFly(self.PluginHook):
            restype = c_float
            argtypes = [c_void_p]

            def hook_function(_self, a1):
                return _self.original(a1) * self.percent

        am = AddressManager(self.storage.data, self.logger)
        addrMain = am.get('speedh_main', scan_pattern, sig_main)
        addrFly = am.get('speedh_fly', scan_pattern, sig_fly)
        self.storage.save()
        self.hook_main = SpeedHookMain(addrMain, True)
        self.hook_fly = SpeedHookFly(addrFly, True)
        self.percent = 1.
        api.command.register(command, self.process_command)

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if arg[0] == "set":
                self.percent = float(arg[1])
                return "set to %s" % arg[1]
            elif arg[0] == "get":
                return self.percent
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            return str(e)
