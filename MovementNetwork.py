from ctypes import *
from FFxivPythonTrigger import api, PluginBase
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

command = "@Move"

Vector3 = OffsetStruct({
    'x': c_float,
    'z': c_float,
    'y': c_float,
})
PositionSetPack = OffsetStruct({
    'r': (c_float, 0),
    'unk0': (c_ushort, 0x4),
    'unk1': (c_ushort, 0x6),
    'pos': (Vector3, 0x8),
    'unk2': (c_uint, 0x14),
}, 24)
PositionAdjustPack = OffsetStruct({
    'old_r': (c_float, 0x0),
    'new_r': (c_float, 0x4),
    'unk0': (c_ushort, 0x8),
    'unk1': (c_ushort, 0xA),
    'old_pos': (Vector3, 0xC),
    'new_pos': (Vector3, 0x18),
    'unk2': (c_uint, 0x24),
}, 40)


class MovementNetwork(PluginBase):
    name = "MovementNetwork"

    def __init__(self):
        super().__init__()
        self.floating = 0
        self.no_fall = False
        # self.register_event(f"*", self.search)
        api.XivNetwork.register_makeup("UpdatePositionHandler", self.makeup_set)
        api.XivNetwork.register_makeup("UpdatePositionInstance", self.makeup_adjust)
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.XivNetwork.unregister_makeup("UpdatePositionHandler", self.makeup_set)
        api.XivNetwork.unregister_makeup("UpdatePositionInstance", self.makeup_adjust)
        api.command.unregister(command)

    def search(self, event):
        if event.id.startswith("network/send/"):
            for struct in [PositionSetPack, PositionAdjustPack]:
                if len(event.raw_msg) == sizeof(struct):
                    self.logger(struct.__name__, hex(event.header.msg_type), struct.from_buffer(event.raw_msg))

    def makeup_set(self, header, raw):
        data = PositionSetPack.from_buffer(raw)
        data.pos.z += self.floating
        if self.no_fall: data.unk0 &= 0xf000
        return header, bytearray(data)

    def makeup_adjust(self, header, raw):
        data = PositionAdjustPack.from_buffer(raw)
        data.new_pos.z += self.floating
        data.old_pos.z += self.floating
        if self.no_fall: data.unk0 &= 0xf000
        return header, bytearray(data)

    def process_command(self, args):
        if args:
            if args[0] == 'fall':
                if len(args) < 2:
                    self.no_fall = not self.no_fall
                elif args[1] == 'on':
                    self.no_fall = True
                elif args[1] == 'off':
                    self.no_fall = False
                else:
                    api.Magic.echo_msg("unknown args: %s" % args[1])
                    return
                api.Magic.echo_msg("FeatherFall: [%s]" % ('enable' if self.no_fall else 'disable'))
            elif args[0] == 'float':
                if len(args) < 2:
                    self.floating = 0
                else:
                    try:
                        self.floating = float(args[1])
                    except ValueError:
                        api.Magic.echo_msg("a number is required")
                api.Magic.echo_msg("Floating: [%s]" % self.floating)
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            api.Magic.echo_msg("FeatherFall: [%s]" % ('enable' if self.no_fall else 'disable'))
            api.Magic.echo_msg("Floating: [%s]" % self.floating)
