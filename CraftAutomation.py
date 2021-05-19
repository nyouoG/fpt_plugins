from FFxivPythonTrigger import *
import time

command = "@ca"


class CraftAutomation(PluginBase):
    name = "CraftAutomation"

    def __init__(self):
        super().__init__()
        self.count = 0
        self.register_event('craft_action', self.next_event)
        self.register_event('craft_end', self.next_event)
        api.command.register(command, self.process_command)

    def next_event(self, evt):
        self.count += 1

    def _start(self):
        import XivCraft
        XivCraft.callback = self.new_callback

    def _onunload(self):
        api.command.unregister(command)

    def process_command(self, args):
        import XivCraft
        XivCraft.callback = self.new_callback

    def new_callback(self, ans: str):
        temp = self.count
        me = api.XivMemory.actor_table.get_me()
        if me is None: return
        if ans != "terminate":
            s = ans
        elif me.currentCP >= 40:
            s = '坯料加工'
        else:
            s = '仓促'
        cmd = '/ac "%s"' % s
        api.Magic.macro_command(cmd)
        time.sleep(5)
        if self.count == temp:
            self.logger.debug(f"resend '{s}'")
            self.new_callback(s)
