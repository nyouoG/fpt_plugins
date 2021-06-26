from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import *
import math

ActionSendOpcode = 844  # cn5.45
PositionSetOpcode = 0x326  # cn5.45

skills = {
    7481: -math.pi,  # 月光，背
    7482: math.pi / 2,  # 花车，侧
}

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
ActionSend = OffsetStruct({
    '_unk_ushort0': (c_ushort, 0x0),
    '_unk_ushort1': (c_ushort, 0x2),
    'skill_id': (c_uint, 0x4),
    'cnt': (c_ushort, 0x8),
    '_unk_ushort4': (c_ushort, 0xa),
    '_unk_ushort5': (c_ushort, 0xc),
    '_unk_ushort6': (c_ushort, 0xe),
    'target_id': (c_uint, 0x10),
}, 32)


class AFix(PluginBase):
    name = "AFix"

    def __init__(self):
        super().__init__()
        api.XivNetwork.register_makeup(ActionSendOpcode, self.makeup_action)
        # self.register_event(f'network/send/{ActionSendOpcode}', self.coor_return)

    def _onunload(self):
        api.XivNetwork.unregister_makeup(ActionSendOpcode, self.makeup_action)

    def coor_return(self, event):
        c = api.Coordinate()
        frame_inject.register_once_call(
            api.XivNetwork.send_messages,
            [(PositionSetOpcode, bytearray(PositionSetPack(r=c.r, pos=Vector3(x=c.x, y=c.y, z=c.z))))]
        )

    def makeup_action(self, header, raw):
        d = ActionSend.from_buffer(raw)
        if d.skill_id in skills:
            t = api.XivMemory.actor_table.get_actor_by_id(d.target_id)
            if t is not None:
                t_pos = t.pos
                angle = t_pos.r + skills[d.skill_id]
                api.XivNetwork.send_messages([(PositionSetOpcode, bytearray(PositionSetPack(r=angle, pos=Vector3(
                    x=t_pos.x + math.sin(angle),
                    y=t_pos.y + math.cos(angle),
                    z=t_pos.z))))])
        return header, bytearray(d)
