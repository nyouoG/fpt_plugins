from FFxivPythonTrigger.memory import scan_pattern, StructFactory, write_bytes, read_memory
from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.Storage import get_module_storage
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger import FFxiv_Version, PluginBase, api
from ctypes import c_ubyte, addressof

"""
patch code to skip cutscene in some zone
command:    @cutscene
format:     /e @cutscene [p(patch)/d(dispatch)]
"""

command = "@cutscene"

_logger = Logger("CutsceneSkipper")
_storage = get_module_storage("CutsceneSkipper")
sig = "48 8B 01 8B D7 FF 90 ? ? ? ? 84 C0 ? ? 48 8B 0D ? ? ? ? BA ? ? ? ? 48 83 C1 10 E8 ? ? ? ? 83 78 20 00 ? ?"
addr = AddressManager(_storage.data, _logger).get("addr", scan_pattern, sig)
_storage.save()

_ver_storage = _storage.data[FFxiv_Version]

_code = read_memory(
    StructFactory.OffsetStruct({
        "mark1": (c_ubyte * 2, 0xd),
        "mark2": (c_ubyte * 2, 0x28)
    }), addr)


def is_patched():
    return _code.mark1[:] == [0x90, 0x90]


def patch():
    if _code.mark1[:] != [0x90, 0x90]:
        _ver_storage["original1"] = _code.mark1[:]
    if _code.mark2[:] != [0x90, 0x90]:
        _ver_storage["original2"] = _code.mark2[:]
    _storage.save()

    write_bytes(addressof(_code.mark1), b'\x90' * 2)
    write_bytes(addressof(_code.mark2), b'\x90' * 2)

    return "patch success"


def dispatch():
    if "original1" not in _ver_storage or "original2" not in _ver_storage:
        raise Exception("original code not found, did you patch it?")

    write_bytes(addressof(_code.mark1), bytes(_ver_storage["original1"]))
    write_bytes(addressof(_code.mark2), bytes(_ver_storage["original2"]))

    return "dispatch success"

class CutsceneSkipper(PluginBase):
    name = "Cutscene Skipper"
    git_repo = 'nyouoG/fpt_plugins'
    repo_path = 'CutsceneSkipper.py'
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
            if not arg:
                if is_patched():
                    return dispatch()
                else:
                    return patch()
            if arg[0] == "patch" or arg[0] == "p":
                return patch()
            elif arg[0] == "dispatch" or arg[0] == "d":
                return dispatch()
            else:
                return "unknown arguments {}".format(arg[0])
        except Exception as e:
            return str(e)
