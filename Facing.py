from math import atan2

from FFxivPythonTrigger import *
command = "@Facing" #command

class TestFacing(PluginBase):
    name = "Facing"

    def __init__(self):
        super().__init__()
        frame_inject.register_continue_call(self.work)
        api.command.register(command, self.process_command)
        self.enable = False

    def _onunload(self):
        frame_inject.unregister_continue_call(self.work)
        api.command.unregister(command)

    def work(self):
        if not self.enable:
            return
        t = api.XivMemory.targets.focus
        if t is None:
            t = api.XivMemory.targets.current
        if t is None:
            return
        me = api.Coordinate()
        me.r = atan2(me.x-t.pos.x,  me.y-t.pos.y)

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
        api.Magic.echo_msg("faceing: [%s]" % ('enable' if self.enable else 'disable'))
