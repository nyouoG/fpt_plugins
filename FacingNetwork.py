from ctypes import *
from math import atan2

from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

command = "@Facing"
MovementOpcode = 0x00ea
MovementPack = OffsetStruct({
    'r': (c_float, 0),
    'x': (c_float, 0x8),
    'z': (c_float, 0xc),
    'y': (c_float, 0x10),
}, 24)


def get_r():
    t = api.XivMemory.targets.focus
    if t is None:
        t = api.XivMemory.targets.current
    if t is not None:
        me = api.Coordinate()
        return atan2(me.x - t.pos.x, me.y - t.pos.y)


class FacingNetwork(PluginBase):
    name = "FacingNetwork"

    def __init__(self):
        super().__init__()
        #self.register_event(f"network/send_{MovementOpcode}", self.work)
        api.XivNetwork.register_makeup(MovementOpcode, self.makeup_data)
        api.command.register(command, self.process_command)
        self.enable = False

    def _onunload(self):
        api.XivNetwork.unregister_makeup(MovementOpcode, self.makeup_data)
        api.command.unregister(command)

    # def work(self, event):
    #     self.logger(MovementPack.from_buffer(event.raw_msg))

    def makeup_data(self, header, raw):
        data = MovementPack.from_buffer(raw)
        if self.enable:
            r = get_r()
            if r is not None: data.r = r
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
        if self.enable:
            data = MovementPack(**api.Coordinate().get_data())
            r = get_r()
            if r is not None: data.r = r
            frame_inject.register_once_call(api.XivNetwork.send_messages, [(MovementOpcode, bytearray(data))])
        api.Magic.echo_msg("facing: [%s]" % ('enable' if self.enable else 'disable'))
