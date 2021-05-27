from ctypes import *
from random import random
from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, EnumStruct
import time
import math

command = "@CTT"

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
NPC_Name = "孤树无援"

KEY_CONFIRM = 96
KEY_CANCEL = 110
KEY_LEFT = 100
KEY_UP = 104


class Solver(object):
    def __init__(self):
        self.pool = list(range(MAX))
        self.prev = None
        self.history = list()
        self.step = 10
        self.progress = 10

        self.start_time = 0
        self.time_left = 0
        self.round_times = 0

    def reset(self):
        self.pool = list(range(MAX))
        self.prev = None
        self.history = list()
        self.step = 10
        self.progress = 10

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
        if self.prev is None:
            if random() > 0.5:
                ans = 80
            else:
                ans = 20
        elif len(self.pool) <= 1:
            ans = self.prev
        elif self.progress < 5 and [i for i in self.history if i[1] == "Great"]:
            ans = [i[0] for i in self.history if i[1] == "Great"][-1]
        else:
            if random() > 0.5:
                ans = [i for i in reversed(self.pool) if abs(i - self.pool[-1]) <= self.step][-1]
            else:
                ans = [i for i in self.pool if abs(i - self.pool[0]) <= self.step][-1]
        self.prev = ans
        return self.prev

    def start_time_reset(self):
        self.start_time = time.time() + 1.5

    def time_check(self, round_status):
        self.time_left = 60 - (time.time() - self.start_time)
        if round_status == "Start Next Round":
            # send
            if self.time_left < 2:
                return False
        elif round_status == 1:
            # recv
            self.round_times += 1
            if self.time_left < 16 or self.round_times >= 6:
                self.start_time = 0
                self.round_times = 0
                return False
        return True


def end_this_time():
    time.sleep(2)
    api.SendKeys.key_press(KEY_CONFIRM)  # confirm
    time.sleep(3)
    # api.SendKeys.key_press(500, 100)  # esc
    for i in range(3):
        api.SendKeys.key_press(KEY_CANCEL, 100)  # cancel
        time.sleep(0.5)


def continue_game():
    time.sleep(5)
    api.SendKeys.key_press(KEY_LEFT)  # left
    time.sleep(0.5)
    api.SendKeys.key_press(KEY_CONFIRM)  # confirm


def felling_limb(status):
    wait = 3
    if status == "Start Next Round":
        wait = 0.2
    elif status != "Felling":
        wait = 1.85
    time.sleep(wait)
    for i in range(5):
        api.SendKeys.key_press(KEY_CONFIRM)  # confirm
        time.sleep(0.2)


def find_nearest_tree():
    nearest = [None, ]
    nearest_dis = 9999
    me_pos = api.XivMemory.actor_table.get_me().pos

    def check(a):
        dis = math.sqrt((a.pos.x - me_pos.x) ** 2 + (a.pos.y - me_pos.y) ** 2 + (a.pos.z - me_pos.z) ** 2)
        if dis > nearest_dis:
            nearest[0] = a

    for i, a1, a2 in api.XivMemory.actor_table.get_item():
        check(a1)
        if a2 is not None:
            check(a2)
    return nearest[0]


def start_new_game():
    api.XivMemory.targets.set_current(find_nearest_tree())
    time.sleep(1)
    api.SendKeys.key_press(KEY_CONFIRM)  # confirm
    api.SendKeys.key_press(KEY_CONFIRM)  # confirm
    time.sleep(1)
    api.SendKeys.key_press(KEY_UP)  # confirm
    api.SendKeys.key_press(KEY_CONFIRM)  # confirm


class CutTheTree(PluginBase):
    name = "CutTheTree"

    def __init__(self):
        super().__init__()
        self.enable = False
        self.enable_hackkkkkk = False
        self.backup = None

        global KEY_UP, KEY_CONFIRM, KEY_CANCEL, KEY_LEFT
        KEY_UP = self.storage.data.setdefault("KEY_UP", 104)
        KEY_CONFIRM = self.storage.data.setdefault("KEY_CONFIRM", 96)
        KEY_CANCEL = self.storage.data.setdefault("KEY_CANCEL", 110)
        KEY_LEFT = self.storage.data.setdefault("KEY_LEFT", 100)
        self.storage.save()

        self.solver = Solver()

        self.register_event('network/recv_789', self.recv_work)
        self.register_event('network/send_843', self.send_work)
        api.XivNetwork.register_makeup(843, self.makeup_data)
        api.command.register(command, self.process_command)

    def process_command(self, args):
        if args:
            if args[0] == 'on':
                self.enable = True
            elif args[0] == 'off':
                self.enable = False
            elif args[0] == 'hack':
                self.enable_hackkkkkk=not self.enable_hackkkkkk
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            self.enable = not self.enable
        msg="CutTheTree: [%s]" % ('enable' if self.enable else 'disable')
        if self.enable_hackkkkkk:msg+="[Hackkkkkkkkkkk]"
        api.Magic.echo_msg(msg)

    def _onunload(self):
        api.XivNetwork.unregister_makeup(843, self.makeup_data)
        api.command.unregister(command)

    def recv_work(self, event):
        data = recv_packet.from_buffer(event.raw_msg)
        res = data.cut_result.value()
        if res is not None:
            self.logger.debug(f"Felling >> {res} ({10 - data.progress_result}/10)")
            self.solver.score(res, data.progress_result)
            if data.progress_result and self.enable_hackkkkkk:
                self.backup.param = self.solver.solve()
                api.XivNetwork.send_messages([(843,bytearray(self.backup))])
        if data.round == 1 and self.enable:
            if self.solver.time_check(data.round):
                self.logger("Go to Next One, Current Profit:" + str(data.current_profit))
                continue_game()
            else:
                self.logger("Game End, Get Profit:{}, Time Left:{}"
                            .format(str(data.current_profit), self.solver.time_left))
                end_this_time()
                start_new_game()

    def send_work(self, event):
        data = send_packet.from_buffer(event.raw_msg)
        msg = data.game_state.value()
        if msg == "Felling" or msg == "Difficulty choice": msg = f"{msg} << {data.param}"

        self.logger.debug(msg)

        key = data.game_state.value()
        if key == "Start Next Round":
            # 选择继续花费的时间
            self.solver.start_time += 4.5
        elif key == "Felling":
            self.backup = data
        if self.enable:
            felling_limb(key)
            if self.solver.time_check(key) is False:
                self.logger("Too African")
                time.sleep(3)
                start_new_game()
        pass

    def makeup_data(self, header, raw):
        data = send_packet.from_buffer(raw)
        key = data.game_state.value()
        if key == "Start Game" or key == "Start Next Round":
            self.solver.reset()
        elif key == "Difficulty choice":
            data.param = 2
            self.solver.start_time_reset()
        elif key == "Felling":
            data.param = self.solver.solve()
        return header, bytearray(data)
