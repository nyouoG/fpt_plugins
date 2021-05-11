from FFxivPythonTrigger import *
import time

command = "@ca"


class CraftAutomation(PluginBase):
    name = "CraftAutomation"

    def __init__(self):
        super().__init__()
        self.count = 0
        api.command.register(command, self.process_command)

    def _start(self):
        import XivCraft
        XivCraft.callback = self.new_callback

    def _onunload(self):
        api.command.unregister(command)

    def process_command(self, args):
        import XivCraft
        XivCraft.callback = self.new_callback

    def new_callback(self, ans: str):
        temp = self.count + 1
        self.count += 1
        cmd = '/ac "%s"' % (ans if ans != "terminate" else '坯料加工')
        api.Magic.macro_command(cmd)
        time.sleep(10)
        if self.count == temp:
            api.Magic.macro_command(cmd)
