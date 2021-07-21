from ctypes import c_float, c_int64, c_ubyte

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_address

command = "@fat"
sig = "E8 ? ? ? ? F3 0F 58 F0 F3 0F 10 05 ? ? ? ?"


class EveryoneFat(PluginBase):
    name = "EveryoneFat"
    git_repo = 'nyouoG/fpt_plugins'
    repo_path = 'EveryoneFat.py'
    hash_path = __file__

    def __init__(self):
        super().__init__()
        self.fatten = 0.

        class ActorHitboxGetHook(Hook):
            restype = c_float
            argtypes = [c_int64, c_ubyte]

            def hook_function(_self, *args):
                return _self.original(*args) + self.fatten

        addr = AddressManager(self.storage.data, self.logger).get('actor_hitbox_get', scan_address, sig, cmd_len=5)
        self.actor_hitbox_get_hook = ActorHitboxGetHook(addr)
        self.storage.save()
        api.command.register(command, self.process_command)

    def _start(self):
        self.actor_hitbox_get_hook.install()

    def _onunload(self):
        api.command.unregister(command)
        self.actor_hitbox_get_hook.uninstall()

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if arg[0] == "set":
                temp = self.fatten
                self.fatten = float(arg[1])
                if not self.fatten and self.actor_hitbox_get_hook.is_enabled:
                    self.actor_hitbox_get_hook.disable()
                elif self.fatten and not self.actor_hitbox_get_hook.is_enabled:
                    self.actor_hitbox_get_hook.enable()
                return f"{temp}=>{self.fatten}"
            elif arg[0] == "get":
                return self.fatten
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            return str(e)
