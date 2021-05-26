from FFxivPythonTrigger import *
import math
from FFxivPythonTrigger.memory import write_ubytes

command = "@tpKill"

"""
ToDo:???
"""

def get_pos():
    me = api.Coordinate()
    return (me.x, me.y, me.z)


def get_dis(p1, p2):
    d1 = p1[0] - p2[0]
    d2 = p1[1] - p2[1]
    d3 = p1[2] - p2[2]
    return math.sqrt(d1 * d1 + d2 * d2 + d3 * d3)


class TpKiller(PluginBase):
    name = "TpKiller"

    def __init__(self):
        super().__init__()
        self.enable = False
        self.test = True
        self.val = 20.0
        self.last = (0, 0, 0)
        self.register_event("log_event", self.deal_chat_log)
        frame_inject.register_continue_call(self.work)
        api.command.register(command, self.process_command)

    def try_kill(self,reason):
        if self.test:
            api.Magic.echo_msg("kill!!! %s" % reason)
        else:
            write_ubytes(frame_inject.address, bytearray(b'\x90' * 99))

    def deal_chat_log(self, event):
        if self.enable:
            for tag in event.chat_log.grouped_sender:
                if tag.Type == "Text" and "游戏管理员" in tag.text():
                    self.try_kill(f"found dangerous chat in [{event}]")
                    return

    def work(self):
        if self.enable:
            new = get_pos()
            dis = get_dis(new, self.last)
            if dis > self.val:
                self.try_kill(f"{dis} move in a frame")
            self.last = new

    def _onunload(self):
        frame_inject.unregister_continue_call(self.work)
        api.command.unregister(command)

    def process_command(self, args):
        if args:
            if args[0] == 'on':
                self.enable = True
                self.last = get_pos()
            elif args[0] == 'off':
                self.enable = False
            elif args[0] == 'test':
                self.test = True
            elif args[0] == 'kill':
                self.test = False
            elif args[0] == 'set':
                self.val = float(args[1])
            else:
                api.Magic.echo_msg("unknown args: %s" % args[0])
        else:
            self.enable = not self.enable
        msg = "TpKiller: [%s][%spf]" % ('enable' if self.enable else 'disable', self.val)
        if self.test: msg += "[test mode]"
        api.Magic.echo_msg(msg)
