from FFxivPythonTrigger.memory import scan_pattern, write_float,read_float
from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.Storage import get_module_storage
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger import PluginBase, api

"""
change the jump value to let you jump higher -- or lower
command:    @sjump
format:     /e @sjump [func] [args]...
functions (*[arg] is optional args):
    [get]:      get current jump value
    [set]:      set current jump value
                format: /e @sjump set [value(float) / "default"]
"""

command = "@sjump"

_logger = Logger("SuperJump")
_storage = get_module_storage("SuperJump")
sig = "66 66 26 41"
addr = AddressManager(_storage.data, _logger).get("sjump", scan_pattern, sig)
_storage.save()

default = 10.4

class SuperJump(PluginBase):
    name = "Super Jumper"
    git_repo = 'nyouoG/fpt_plugins'
    repo_path = 'SuperJump.py'
    hash_path = __file__

    def __init__(self):
        super().__init__()
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if arg[0] == "set":
                if arg[1] == 'default':
                    arg[1] = default
                write_float(addr, float(arg[1]))
                return "set to %s" % arg[1]
            elif arg[0] == "get":
                return read_float(addr)
            else:
                return "unknown arg [%s]" % arg[0]
        except Exception as e:
            return str(e)
