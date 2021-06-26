from shapely.geometry import Point

from FFxivPythonTrigger import *
from FFxivPythonTrigger.Utils import sector
from FFxivPythonTrigger.memory.StructFactory import *
from shapely.ops import cascaded_union, nearest_points

import math

ActionSendOpcode = 844  # cn5.45
PositionSetOpcode = 0x326  # cn5.45

FRONT = 1
SIDE = 2
BACK = 3

skills = {
    7481: BACK,  # 月光，背
    7482: SIDE,  # 花车，侧
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

angle = math.pi / 2 - 0.1


def get_nearest(me_pos, target, mode, dis=3):
    radius = target.HitboxRadius + dis - 0.5
    if mode == SIDE:
        area1 = sector(target.pos.x, target.pos.y, radius, angle, target.pos.r + math.pi / 2)
        area2 = sector(target.pos.x, target.pos.y, radius, angle, target.pos.r - math.pi / 2)
        area = cascaded_union([area1, area2])
    elif mode == FRONT:
        area = sector(target.pos.x, target.pos.y, radius, angle, target.pos.r)
    elif mode == BACK:
        area = sector(target.pos.x, target.pos.y, radius, angle, target.pos.r - math.pi)
    else:
        area = target.hitbox

    area = area.difference(Point(target.pos.x, target.pos.y).buffer(0.5))
    me = Point(me_pos.x, me_pos.y)
    p1 = me if area.contains(me) else nearest_points(area, me)[0]
    return p1.x, p1.y


class AFix(PluginBase):
    name = "AFix"

    def __init__(self):
        super().__init__()
        self.last_reset = perf_counter()
        api.XivNetwork.register_makeup(ActionSendOpcode, self.makeup_action)
        self.register_event(f'network/action_effect', self.coor_return)

    def _onunload(self):
        api.XivNetwork.unregister_makeup(ActionSendOpcode, self.makeup_action)

    def coor_return(self, evt):
        if self.last_reset + 1 > perf_counter() or evt.source_id != api.XivMemory.actor_table.get_me().id or evt.action_type != 'action' or evt.action_id not in skills:
            return
        c = api.Coordinate()
        frame_inject.register_once_call(
            api.XivNetwork.send_messages,
            [(PositionSetOpcode, bytearray(PositionSetPack(r=c.r, pos=Vector3(x=c.x, y=c.y, z=c.z))))]
        )
        self.last_reset = perf_counter()

    def makeup_action(self, header, raw):
        d = ActionSend.from_buffer(raw)
        if d.skill_id in skills:
            t = api.XivMemory.actor_table.get_actor_by_id(d.target_id)
            if t is not None:
                new_x, new_y = get_nearest(api.Coordinate(), t, skills[d.skill_id])
                msg = PositionSetPack(r=t.pos.r, pos=Vector3(x=new_x, y=new_y, z=t.pos.z))
                api.XivNetwork.send_messages([(PositionSetOpcode, bytearray(msg))])
        return header, bytearray(d)
