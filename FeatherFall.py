from ctypes import *
from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

command = "@Feather"

MovementOpcode = 0x00ea
MovementPack = OffsetStruct({
    'unk1': (c_ushort, 0x4),
}, 24)

Movement2Opcode = 0x0154
Movement2Pack = OffsetStruct({
    'unk0': (c_ushort,0x8),
}, 40)

class FeatherFall(PluginBase):
    name = "FeatherFall"

    def __init__(self):
        super().__init__()
        api.XivNetwork.register_makeup(MovementOpcode, self.makeup_data)
        api.XivNetwork.register_makeup(Movement2Opcode, self.makeup_data2)
        api.command.register(command, self.process_command)
        self.enable = False

    def _onunload(self):
        api.XivNetwork.unregister_makeup(Movement2Opcode, self.makeup_data2)
        api.command.unregister(command)

    def makeup_data(self, header, raw):
        data = MovementPack.from_buffer(raw)
        if self.enable:
            data.unk1 &= 0xf000
        return header, bytearray(data)

    def makeup_data2(self, header, raw):
        data = Movement2Pack.from_buffer(raw)
        if self.enable:
            data.unk0 &= 0xf000
        return header, bytearray(data)

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
        api.Magic.echo_msg("FeatherFall: [%s]" % ('enable' if self.enable else 'disable'))
