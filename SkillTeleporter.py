from ctypes import *
from math import *
from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

command = "@stp"

PositionSetOpcode = 0x326  # cn5.45
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

MAX = 150


class SkillTeleporter(PluginBase):
    name = "SkillTeleporter"
    next: Optional[tuple[float, float, float]]

    def __init__(self):
        super().__init__()
        self.next = None
        api.XivNetwork.register_makeup(PositionSetOpcode, self.makeup_action)
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.XivNetwork.unregister_makeup(PositionSetOpcode, self.makeup_action)
        api.command.unregister(command)

    def process_command(self, args):
        try:
            self.next = (float(args[0]), float(args[1]), float(args[2]))
        except:
            self.next = None
            raise

    def get_next(self):
        c = api.Coordinate()
        x = c.x - self.next[0]
        y = c.y - self.next[1]
        z = c.z - self.next[2]
        r = sqrt(x ** 2 + y ** 2 + z ** 2)
        if r <= MAX:
            temp = self.next[0], self.next[1], self.next[2]
            self.next = None
            return temp
        p = acos(z / r)
        a = atan(y / x)
        return c.x - MAX * sin(p) * cos(a), c.y - MAX * sin(p) * sin(a), c.z - MAX * cos(p)

    def makeup_action(self, header, raw):
        msg = PositionSetPack.from_buffer(raw)
        if msg.unk0 == 0x1000 and self.next is not None:
            c = api.Coordinate()
            c.x, c.y, c.z = msg.pos.x, msg.pos.y, msg.pos.z = self.get_next()
        return header, bytearray(msg)
