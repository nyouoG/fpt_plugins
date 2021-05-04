from FFxivPythonTrigger import PluginBase, api, frame_inject
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_address, read_memory, scan_pattern
from FFxivPythonTrigger.memory.StructFactory import PointerStruct, OffsetStruct
from ctypes import *
import math

"""

tele~port~er~~~

command:    @tp
format:     /e @tp [func] [args]...
functions (*[arg] is optional args):
    [get]:          get current coordinates
    
    [set]:          set current coordinates
                    format: /e @tp set [x:float] [y:float] [z:float]
                    
    [list]:         list saved coordinates in current zone
    
    [save]:         save coordinates with a name
    
                    format: /e @tp save [name:str]
    [drop]:         drop a saved coordinates
    
                    format: /e @tp drop [name:str]
                    
    [goto]:         goto a saved coordinates with 15 meters limit
                    format: /e @tp goto [name:str]
                    
    [force-goto]:   goto a saved coordinates with no distance limit
                    format: /e @tp force-goto [name:str]

    relative coordinates teleport:
        format: /e @tp [direction] [distance:float]
        direction:  u/up,
                    d/down,
                    f/front,
                    l/left,
                    r/right,
                    b/back,
                    n/north,
                    e/east,
                    w/west,
                    s/south
"""

command = "@tp"
pattern_main = "f3 0f ?? ?? ?? ?? ?? ?? eb ?? 48 8b ?? ?? ?? ?? ?? e8 ?? ?? ?? ?? 48 85"
pattern_fly = "48 8d ?? ?? ?? ?? ?? 84 c0 75 ?? 48 8d ?? ?? ?? ?? ?? 80 79 66 ?? 74 ?? e8 ?? ?? ?? ?? c6 87 f4 03 ?? ??"
pattern_actor_move = "40 53 48 83 EC ? F3 0F 11 89 ? ? ? ? 48 8B D9 F3 0F 11 91 ? ? ? ?"

Vector = OffsetStruct({
    "x": (c_float, 0),
    "y": (c_float, 8),
    "z": (c_float, 4),
    "r": (c_float, 16),
})

MainCoor = PointerStruct(Vector, 160)


class Teleporter(PluginBase):
    name = "Teleporter"

    def __init__(self):
        super().__init__()
        am = AddressManager(self.storage.data, self.logger)
        ptr_main = am.get("main ptr", scan_address, pattern_main, add=0x14, cmd_len=8)
        addr_fly = am.get("fly addr", scan_address, pattern_fly, cmd_len=7, add=16)
        self.storage.save()

        self._coor_main = read_memory(MainCoor, ptr_main)
        self.coor_fly = read_memory(Vector, addr_fly)

        api.command.register(command, self.process_command)
        self.lock_coor = None

    @property
    def coor_main(self):
        return self._coor_main.value

    def _onunload(self):
        api.command.unregister(command)

    def tp(self, x=None, y=None, z=None):
        if self.coor_main is not None:
            if x is not None:
                self.coor_main.x = x
                self.coor_fly.x = x
            if y is not None:
                self.coor_main.y = y
                self.coor_fly.y = y
            if z is not None:
                self.coor_main.z = z
                self.coor_fly.z = z

    def tp_rxy(self, angle, dis):
        frame_inject.register_once_call(self.tp, x=self.coor_main.x + (math.sin(angle) * dis), y=self.coor_main.y + (math.cos(angle) * dis))

    def tp_rz(self, dis):
        frame_inject.register_once_call(self.tp, z=self.coor_main.z + dis)

    def get_zone_data(self):
        zid = api.XivMemory.zone_id
        data = self.storage.data.setdefault(str(zid), dict())
        return zid, data

    def _process_command(self, args):
        a1 = args[0].lower()
        if a1 == "set":
            return self.tp(float(args[1]), float(args[2]), float(args[3]))
        elif a1 == "get":
            return "%.2f %.2f %.2f" % (self.coor_main.x, self.coor_main.y, self.coor_main.z)
        elif a1 == "list":
            zid, data = self.get_zone_data()
            return "%s (%s): %s" % (zid, len(data), '/'.join(data.keys()))
        elif a1 == "save":
            zid, data = self.get_zone_data()
            if args[1] in data:
                return "key [%s] is already in zone [%s]" % (args[1], zid)
            data[args[1]] = [self.coor_main.x, self.coor_main.y, self.coor_main.z]
            self.storage.save()
            return "%s (%s): %s" % (zid, len(data), '/'.join(data.keys()))
        elif a1 == "goto":
            zid, data = self.get_zone_data()
            if args[1] not in data:
                return "key [%s] is not in zone [%s]" % (args[1], zid)
            dis = math.sqrt((data[args[1]][0] - self.coor_main.x) ** 2 + (data[args[1]][1] - self.coor_main.y) ** 2)
            if dis >= 15:
                return "target point is %.2f meters far, teleport to target is a dangerous operation,please use 'force-goto'" % dis
            frame_inject.register_once_call(self.tp, *data[args[1]])
            return "success"
        elif a1 == "force-goto" or a1 == "fgoto":
            zid, data = self.get_zone_data()
            if args[1] not in data:
                return "key [%s] is not in zone [%s]" % (args[1], zid)
            frame_inject.register_once_call(self.tp, *data[args[1]])
            return "success"
        elif a1 == "drop":
            zid, data = self.get_zone_data()
            if args[1] not in data:
                return "key [%s] is not in zone [%s]" % (zid, args[1])
            del data[args[1]]
            self.storage.save()
            return "success"
        dis = float(args[1])
        if a1 in ["north", "n"]:
            self.tp_rxy(math.pi, dis)
            return "tp to north %s" % dis
        elif a1 in ["east", "e"]:
            self.tp_rxy(math.pi / 2, dis)
            return "tp to east %s" % dis
        elif a1 in ["west", "w"]:
            self.tp_rxy(math.pi / -2, dis)
            return "tp to west %s" % dis
        elif a1 in ["south", "s"]:
            self.tp_rxy(0, dis)
            return "tp to south %s" % dis
        elif a1 in ["front", "f"]:
            self.tp_rxy(self.coor_main.r, dis)
            return "tp to front %s" % dis
        elif a1 in ["back", "b"]:
            self.tp_rxy(self.coor_main.r - math.pi, dis)
            return "tp to back %s" % dis
        elif a1 in ["left", "l"]:
            self.tp_rxy(self.coor_main.r + math.pi / 2, dis)
            return "tp to left %s" % dis
        elif a1 in ["right", "r"]:
            self.tp_rxy(self.coor_main.r - math.pi / 2, dis)
            return "tp to right %s" % dis
        elif a1 in ["up", "u"]:
            self.tp_rz(dis)
            return "tp to up %s" % dis
        elif a1 in ["down", "d"]:
            self.tp_rz(-dis)
            return "tp to down %s" % dis
        else:
            return "unknown direction: [%s]" % a1

    def process_command(self, args):
        try:
            msg = self._process_command(args)
            if msg is not None:
                api.Magic.echo_msg(msg)
        except Exception as e:
            api.Magic.echo_msg(str(e))
