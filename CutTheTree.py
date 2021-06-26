from ctypes import *
from random import random
from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, EnumStruct

command = "@CTT"

recv_opcode = 0x360  # cn5.45
send_opcode = 0x39d  # cn5.45

# recv_opcode = 789  # cn5.41
# send_opcode = 843  # cn5.41

recv_packet = OffsetStruct({
    'cut_result': (EnumStruct(c_ubyte, {
        0x0: "Fail",
        0x1: "Normal",
        0x2: "Great",
        0x3: "Perfect"
    }), 12),
    'progress_result': (c_ubyte, 16),
    'round': (c_ubyte, 28),
    'current_profit': (c_ushort, 36),
    'future_profit': (c_ushort, 40),
})
send_packet = OffsetStruct({
    'game_state': (EnumStruct(c_ubyte, {
        0x07: "Start Game",
        0x09: "Difficulty choice",
        0x0A: "Felling",
        0x0B: "Start Next Round"
    }), 6),
    'param': (c_ubyte, 8)
}, 16)

MAX = 101


class Solver(object):
    def __init__(self):
        self.pool = self.history = list()
        self.prev = self.step = self.progress = self.count = 0
        self.reset()

    def reset(self):
        self.pool = list(range(MAX))
        self.prev = None
        self.history = list()
        self.step = 10
        self.progress = 10
        self.count = 0

    def score(self, score, progress):
        self.progress = progress
        self.history.append((self.prev, score))
        if score == "Fail":
            self.pool = [i for i in self.pool if abs(i - self.prev) > 20]
        elif score == "Normal":
            self.pool = [i for i in self.pool if 10 <= abs(i - self.prev) <= 20]
            self.step = min(self.step, 5)
        elif score == "Great":
            self.pool = [i for i in self.pool if 0 < abs(i - self.prev) <= 10]
            self.step = min(self.step, 3)
        elif score == "Perfect":
            self.pool = [self.prev]

    def solve(self):
        self.count += 1
        if self.count >= 9:
            return
        if self.prev is None:
            ans = 80 if random() > 0.5 else 20
        elif len(self.pool) <= 1:
            ans = self.prev
        elif self.progress < 5 and [i for i in self.history if i[1] == "Great"]:
            ans = [i[0] for i in self.history if i[1] == "Great"][-1]
        else:
            p, s = (self.pool, self.pool[0]) if random() > 0.5 else (reversed(self.pool), self.pool[-1])
            ans = [i for i in p if abs(i - s) <= self.step][-1]
        self.prev = ans
        return self.prev


class CutTheTree(PluginBase):
    name = "CutTheTree"

    def __init__(self):
        super().__init__()
        self.enable = False
        self.backup_fell = None
        self.backup_next = None

        self.solver = Solver()

        self.register_event(f'network/recv/{recv_opcode}', self.recv_work)
        self.register_event(f'network/send/{send_opcode}', self.send_work)
        api.XivNetwork.register_makeup(send_opcode, self.makeup_data)
        api.command.register(command, self.process_command)

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
        api.Magic.echo_msg("CutTheTree: [%s]" % ('enable' if self.enable else 'disable'))

    def _onunload(self):
        api.XivNetwork.unregister_makeup(send_opcode, self.makeup_data)
        api.command.unregister(command)

    def send(self, msg):
        frame_inject.register_once_call(api.XivNetwork.send_messages, [(send_opcode, bytearray(msg))])

    def send_fell(self):
        if self.backup_fell is not None:
            ans = self.solver.solve()
            if ans is None:
                return
            self.backup_fell.param = ans
            self.send(self.backup_fell)

    def recv_work(self, event):
        data = recv_packet.from_buffer(event.raw_msg)
        res = data.cut_result.value()
        if res is not None:
            self.logger.debug(f"Felling >> {res} ({10 - data.progress_result}/10)")
            self.solver.score(res, data.progress_result)
            if self.enable:
                if data.progress_result:
                    self.send_fell()
                elif data.future_profit and self.backup_next is not None:
                    self.send(self.backup_next)
                else:
                    api.Magic.echo_msg("Cut!")

    def send_work(self, event):
        data = send_packet.from_buffer(event.raw_msg)
        msg = data.game_state.value()
        if msg == "Felling" or msg == "Difficulty choice":
            msg = f"{msg} << {data.param}"
        self.logger.debug(msg)
        key = data.game_state.value()
        if key == "Difficulty choice" or key == "Start Next Round":
            self.solver.reset()
        if key == "Start Next Round":
            self.backup_next = data
            if self.enable:
                self.send_fell()
        elif key == "Difficulty choice":
            if self.enable:
                self.send_fell()
        elif key == "Felling":
            self.backup_fell = data

    def makeup_data(self, header, raw):
        data = send_packet.from_buffer(raw)
        key = data.game_state.value()
        if key == "Difficulty choice":
            data.param = 2
        elif key == "Felling":
            ans = self.solver.solve()
            if ans is not None:
                data.param = ans
        return header, bytearray(data)

# import math
#
# NPC_Name = "孤树无援"
#
#
# def dis(a, b):
#     return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)
#
#
# def find_nearest_tree():
#     nearest = [None, ]
#     nearest_dis = 9999
#     me_pos = api.XivMemory.actor_table.get_me().pos
#
#     for i, a1, a2 in api.XivMemory.actor_table.get_item():
#         dis1 = dis(me_pos, a1.pos)
#         if dis1 < nearest_dis:
#             nearest[0] = a1
#             nearest_dis = dis1
#         if a2 is not None:
#             dis2 = dis(me_pos, a2.pos)
#             if dis2 < nearest_dis:
#                 nearest[0] = a2
#                 nearest_dis = dis2
#     return nearest[0]
