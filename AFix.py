from shapely.geometry import Point

from FFxivPythonTrigger import *
from FFxivPythonTrigger.Utils import sector
from FFxivPythonTrigger.memory.StructFactory import *
from shapely.ops import cascaded_union, nearest_points

import math

FRONT = 1
SIDE = 2
BACK = 3

skills = {
    7481: BACK,  # 月光，背
    7482: SIDE,  # 花车，侧
    53: BACK,  # 连击，背，武僧
    54: BACK,  # 正拳，背，武僧
    56: SIDE,  # 崩拳，侧，武僧
    61: SIDE,  # 双掌打，侧，武僧
    66: BACK,  # 破碎拳，背，武僧
    74: SIDE,  # 双龙脚，侧，武僧
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
PositionAdjustPack = OffsetStruct({
    'old_r': (c_float, 0x0),
    'new_r': (c_float, 0x4),
    'unk0': (c_ushort, 0x8),
    'unk1': (c_ushort, 0xA),
    'old_pos': (Vector3, 0xC),
    'new_pos': (Vector3, 0x18),
    'unk2': (c_uint, 0x24),
}, 40)

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
    if area.contains(me):
        return None
    p1 = nearest_points(area, me)[0]
    return p1.x, p1.y


class AFix(PluginBase):
    name = "AFix"

    def __init__(self):
        super().__init__()
        self.last_reset = perf_counter()
        api.XivNetwork.register_makeup("ActionSend", self.makeup_action)
        self.register_event(f'network/action_effect', self.coor_return)
        self.work = False
        self.adjust_mode = True
        self.adjust_sig = 0
        self.set_sig = 0x93
        self.register_event('network/position_adjust', self.deal_adjust)
        self.register_event('network/position_set', self.deal_set)

    def _onunload(self):
        api.XivNetwork.unregister_makeup("ActionSend", self.makeup_action)

    def deal_adjust(self, evt):
        self.adjust_mode = True
        self.adjust_sig = evt.raw_msg.unk1 & 0xf

    def deal_set(self, evt):
        self.adjust_mode = False
        if not (evt.raw_msg.unk0 or evt.raw_msg.unk1) and 0x10000 > evt.raw_msg.unk2 > 0:
            self.set_sig = evt.raw_msg.unk2

    def goto(self, new_x=None, new_y=None, new_r=None, stop=False):
        c = api.Coordinate()
        if new_r is None:
            new_r = c.r
        target = Vector3(x=new_x if new_x is not None else c.x, y=new_y if new_y is not None else c.y, z=c.z)
        if self.adjust_mode:
            msg = PositionAdjustPack(old_r=c.r, new_r=new_r, old_pos=target, new_pos=target, unk0=(0x4000 if stop else 0),
                                     unk1=(0x40 if stop else 0) | self.adjust_sig)
            code = "UpdatePositionInstance"
        else:
            msg = PositionSetPack(r=new_r, pos=target, unk2=self.set_sig if stop else 0)
            code = "UpdatePositionHandler"
        self.logger('goto', target, new_r, hex(msg.unk0), hex(msg.unk1), hex(msg.unk2))
        api.XivNetwork.send_messages([(code, bytearray(msg))], False)

    def coor_return(self, evt):
        if not self.work or evt.source_id != api.XivMemory.actor_table.get_me().id or evt.action_type != 'action' or evt.action_id not in skills:
            return
        self.goto(stop=True)
        self.work = False

    def makeup_action(self, header, raw):
        d = ActionSend.from_buffer(raw)
        if d.skill_id in skills and 1250 not in api.XivMemory.actor_table.get_me().effects.get_dict():
            t = api.XivMemory.actor_table.get_actor_by_id(d.target_id)
            if t is not None:
                xy = get_nearest(api.Coordinate(), t, skills[d.skill_id])
                if xy is not None:
                    new_r = api.Coordinate().r
                    new_r = new_r + (-math.pi if new_r > 0 else math.pi)
                    self.work = True
                    self.goto(*xy, new_r)
        return header, bytearray(d)
