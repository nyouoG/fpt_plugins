from ctypes import *
from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, EnumStruct

recv_packet = OffsetStruct({
    'cut_result': (EnumStruct(c_ubyte, {0x0: "Fail", 0x1: "Normal", 0x2: "Great", 0x3: "Perfect"}), 44),
    'progress_result': (c_ubyte, 48),
    'round': (c_ubyte, 60),
    'current_profit': (c_ubyte, 68),
    'future_profit': (c_ubyte, 72),
})
send_packet = OffsetStruct({
    'game_state': (EnumStruct(c_ubyte, {0x07: "Start Game", 0x09: "Difficulty choice", 0x0A: "Felling", 0x0B: "Start Next Round"}), 38),
    'param': (c_ubyte, 40)
})


class Solver(object):
    def __init__(self):
        self.pool = list(range(91))
        self.prev = None
        self.history = list()
        self.step = 20

    def reset(self):
        self.pool = list(range(91))
        self.prev = None
        self.history = list()
        self.step = 20

    def score(self, score):
        self.history.append(score)
        if score == "Fail":
            self.pool = [i for i in self.pool if abs(i - self.prev) > 20]
        elif score == "Normal":
            self.pool = [i for i in self.pool if 10 < abs(i - self.prev) <= 20]
            self.step = min(self.step, 5)
        elif score == "Great":
            self.pool = [i for i in self.pool if abs(i - self.prev) <= 10]
            self.step = min(self.step, 1)
        elif score == "Perfect":
            self.pool = [self.prev]

    def solve(self):
        if self.prev is None:
            ans = 20
        elif self.history[-1] == "Fail":
            ans = min(self.prev + 35, 90)
        elif len(self.pool) == 1:
            ans = self.pool[0]
        else:
            ans = [i for i in self.pool if abs(i - self.pool[0]) <= self.step][-1]
        self.prev = ans
        return self.prev


class CutTheTree(PluginBase):
    name = "CutTheTree"

    def __init__(self):
        super().__init__()
        self.solver = Solver()
        self.register_event('network/recv_789', self.recv_work)
        self.register_event('network/send_843', self.send_work)
        api.XivNetwork.register_makeup(843, self.makeup_data)
        self.logger("reloaded")

    def _onunload(self):
        api.XivNetwork.unregister_makeup(843, self.makeup_data)

    def recv_work(self, event):
        data = recv_packet.from_buffer(event.raw_msg)
        res = data.cut_result.value()
        if res is not None:
            self.solver.score(res)
        # self.logger(data)

    def send_work(self, event):
        # self.logger(send_packet.from_buffer(event.raw_msg))
        pass

    def makeup_data(self, raw):
        data = send_packet.from_buffer(raw)
        key = data.game_state.value()
        if key == "Start Game" or key == "Start Next Round":
            self.solver.reset()
        elif key == "Difficulty choice":
            data.param = 2
        elif key == "Felling":
            data.param = self.solver.solve()
        return bytearray(data)
