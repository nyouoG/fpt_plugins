from FFxivPythonTrigger import *

from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_address, read_ubyte

command = "@slide"
is_casting_sig = "80 3D ? ? ? ? ? 74 ? 48 8B 03 48 8B CB FF 50 ?"


class Slider(PluginBase):
    name = "Slider"

    def __init__(self):
        super().__init__()
        am = AddressManager(self.storage.data, self.logger)
        self.is_casting_addr = am.get('is_casting', scan_address, is_casting_sig, cmd_len=7, ptr_idx=2, add=1)
        self.storage.save()
        self.is_casting = read_ubyte(self.is_casting_addr)
        self.enable = False
        api.PosLock.register_statement(self.get_result)
        api.command.register(command, self.process_command)

    def get_result(self):
        return self.enable and read_ubyte(self.is_casting_addr)

    def _onunload(self):
        api.command.unregister(command)
        api.PosLock.remove_statement(self.get_result)

    def process_command(self, args):
        if args:
            if args[0] == 'on':
                self.enable = True
            elif args[0] == 'off':
                self.enable = False
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            self.enable = not self.enable
        api.Magic.echo_msg("slider: [%s]" % ('enable' if self.enable else 'disable'))
