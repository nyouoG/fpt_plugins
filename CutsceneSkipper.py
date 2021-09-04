from FFxivPythonTrigger.memory import scan_pattern, StructFactory, write_bytes, read_memory
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger import FFxiv_Version, PluginBase, api
from ctypes import c_ubyte, addressof

"""
patch code to skip cutscene in some zone
command:    @cutscene
format:     /e @cutscene [p(patch)/d(dispatch)]
"""

command = "@cutscene"
sig = "75 33 48 8B 0D ?? ?? ?? ?? BA ?? 00 00 00 48 83 C1 10 E8 ?? ?? ?? ?? 83 78"


class CutsceneSkipper(PluginBase):
    name = "Cutscene Skipper"
    git_repo = 'nyouoG/fpt_plugins'
    repo_path = 'CutsceneSkipper.py'
    hash_path = __file__

    def is_patched(self):
        return self.code.mark1[:] == [0x90, 0x90]

    def patch(self):
        if self.code.mark1[:] != [0x90, 0x90]:
            self.ver_storage["original1"] = self.code.mark1[:]
        if self.code.mark2[:] != [0x90, 0x90]:
            self.ver_storage["original2"] = self.code.mark2[:]
        self.storage.save()

        write_bytes(addressof(self.code.mark1), b'\x90' * 2)
        write_bytes(addressof(self.code.mark2), b'\x90' * 2)

        return "patch success"

    def dispatch(self):
        if "original1" not in self.ver_storage or "original2" not in self.ver_storage:
            raise Exception("original code not found")

        write_bytes(addressof(self.code.mark1), bytes(self.ver_storage["original1"]))
        write_bytes(addressof(self.code.mark2), bytes(self.ver_storage["original2"]))

        return "dispatch success"

    def __init__(self):
        super().__init__()
        self.code = read_memory(
            StructFactory.OffsetStruct({
                "mark1": (c_ubyte * 2, 0),
                "mark2": (c_ubyte * 2, 0x1b)
            }), AddressManager(self.storage.data, self.logger).get("cskip_addr", scan_pattern, sig))
        self.ver_storage = self.storage.data.setdefault(FFxiv_Version, dict())
        self.storage.save()
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if not arg:
                if self.is_patched():
                    return self.dispatch()
                else:
                    return self.patch()
            if arg[0] == "patch" or arg[0] == "p":
                return self.patch()
            elif arg[0] == "dispatch" or arg[0] == "d":
                return self.dispatch()
            else:
                return "unknown arguments {}".format(arg[0])
        except Exception as e:
            return str(e)
