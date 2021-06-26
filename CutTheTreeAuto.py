from ctypes import *
from random import random
from FFxivPythonTrigger import *
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, EnumStruct
import time

command = "@CTTA"

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

KEY_CONFIRM = 96
KEY_CANCEL = 110
KEY_LEFT = 100
KEY_UP = 104

import math

NPC_Name = "孤树无援"


def dis(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def find_nearest_tree():
    nearest = None
    nearest_dis = 9999
    me_pos = api.XivMemory.actor_table.get_me().pos
    for a1 in api.XivMemory.actor_table.get_actors_by_name(NPC_Name):
        dis1 = dis(me_pos, a1.pos)
        if dis1 < nearest_dis:
            nearest = a1
            nearest_dis = dis1
    return nearest


class Solver(object):
    def __init__(self):
        self.pool = list(range(MAX))
        self.prev = None
        self.history = list()
        self.step = 10
        self.progress = 10
        self.count = 0

        self.start_time = 0
        self.time_left = 0
        self.round_times = 0
        self.last_hit = False

    def reset(self):
        self.pool = list(range(MAX))
        self.prev = None
        self.history = list()
        self.step = 10
        self.progress = 10
        self.count = 0

        self.last_hit = False

    def score(self, score, progress):
        self.progress = progress
        self.history.append((self.prev, score))
        if self.progress == 0:
            self.last_hit = True
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


# 动画锁？反正是个锁，防止多次触发动作的
key_progress = False


def end_this_time():
    global key_progress
    if key_progress:
        return
    else:
        key_progress = True
    time.sleep(3)
    api.SendKeys.key_press(KEY_CONFIRM)  # confirm
    time.sleep(3)
    api.SendKeys.key_press(500, 100)  # esc
    for i in range(3):
        api.SendKeys.key_press(KEY_CANCEL, 100)  # cancel
        time.sleep(0.5)
    key_progress = False


def continue_game():
    global key_progress
    if key_progress:
        return
    else:
        key_progress = True
    time.sleep(5.5)
    api.SendKeys.key_press(KEY_LEFT)  # left
    time.sleep(0.5)
    api.SendKeys.key_press(KEY_CONFIRM)  # confirm
    key_progress = False


def felling_limb(status, enable_hackkkkkk, last_hit):
    wait = 2.5
    if status == "Start Next Round":
        wait = 0.2
    elif status == "Difficulty choice":
        wait = 1.65
    elif status == "Felling" and enable_hackkkkkk and not last_hit:
        return
    time.sleep(wait)
    for i in range(5):
        api.SendKeys.key_press(KEY_CONFIRM)  # confirm
        time.sleep(0.2)





class CutTheTree(PluginBase):
    name = "CutTheTreeAuto"

    def __init__(self):
        super().__init__()
        self.last_profit = 0
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
            elif args[0] == 'hack':
                self.enable_hackkkkkk = not self.enable_hackkkkkk
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            self.enable = not self.enable
        msg = "CutTheTree: [%s]" % ('enable' if self.enable else 'disable')
        if self.enable_hackkkkkk:
            msg += "[Hackkkkkkkkkkk]"
        api.Magic.echo_msg(msg)

    def _onunload(self):
        api.XivNetwork.unregister_makeup(send_opcode, self.makeup_data)
        api.command.unregister(command)

    def hack(self):
        if self.backup is not None:
            ans = self.solver.solve()
            if ans is None:
                return
            self.backup.param = ans
            api.XivNetwork.send_messages([(send_opcode, bytearray(self.backup))])

    def start_new_game(self):
        target = find_nearest_tree()
        if target is not None:
            api.XivMemory.targets.set_current(target)
            api.SendKeys.key_press(KEY_CONFIRM)  # confirm
            api.SendKeys.key_press(KEY_CONFIRM)  # confirm
            time.sleep(1)
            api.SendKeys.key_press(KEY_UP)  # confirm
            api.SendKeys.key_press(KEY_CONFIRM)  # confirm
        else:
            self.logger("no tree found")

    def recv_work(self, event):
        data = recv_packet.from_buffer(event.raw_msg)
        res = data.cut_result.value()
        if res is not None:
            self.logger.debug(f"Felling >> {res} ({10 - data.progress_result}/10)")
            self.solver.score(res, data.progress_result)
            if data.progress_result and self.enable_hackkkkkk:
                self.hack()
        if data.round == 1 and self.enable:
            if self.enable_hackkkkkk:
                end = data.current_profit < 1050
            else:
                end = self.solver.time_check(data.round)

            if end:
                self.logger("Go to Next One, Current Profit:" + str(data.current_profit))
                continue_game()
            else:
                self.logger("Game End, Get Profit:{}, Time Left:{}"
                            .format(str(data.current_profit), self.solver.time_left))
                end_this_time()
                self.start_new_game()

    def send_work(self, event):
        data = send_packet.from_buffer(event.raw_msg)
        msg = data.game_state.value()
        if msg == "Felling" or msg == "Difficulty choice":
            msg = f"{msg} << {data.param}"

        self.logger.debug(msg)

        key = data.game_state.value()
        # 临时解决，可能一会就覆盖了
        last_hit = False
        if key == "Difficulty choice" or key == "Start Next Round":
            last_hit = self.solver.last_hit
            self.solver.reset()
            if self.enable_hackkkkkk:
                self.hack()
        if key == "Start Next Round":
            # 选择继续花费的时间，hack模式会收到两个，直接无视掉时间好了
            self.solver.start_time += 4.5
        elif key == "Felling":
            self.backup = data
        if self.enable:
            felling_limb(key, self.enable_hackkkkkk, last_hit)
            if self.solver.time_check(key) is False and self.enable_hackkkkkk is False:
                self.logger("Too African")
                time.sleep(3)
                self.start_new_game()
        pass

    def makeup_data(self, header, raw):
        data = send_packet.from_buffer(raw)
        key = data.game_state.value()
        if key == "Difficulty choice":
            data.param = 2
            self.solver.start_time_reset()
        elif key == "Felling":
            data.param = self.solver.solve()
        return header, bytearray(data)
