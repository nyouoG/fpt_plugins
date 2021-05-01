from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_pattern, StructFactory, read_ubytes, write_bytes

"""
disable skill animation lock
command:    @sALock
format:     /e @sALock *[p(patch)/d(dispatch)]
"""

sig1 = "F3 0F ? ? ? ? ? ? 41 F6 47 20"
sig2 = "41 C7 45 08 ? ? ? ? EB ? 41 C7 45 08"
length = 8
nop = b"\x90" * length

command = "@sALock"


class SkillAniUnlocker(PluginBase):
    name = "skill animation unlocker"

    def __init__(self):
        super().__init__()
        am = AddressManager(self.storage.data, self.logger)
        self.addr1 = am.get('addr1', scan_pattern, sig1)
        self.addr2 = am.get('addr2', scan_pattern, sig2)
        self.storage.save()
        self.originals = [
            bytes(read_ubytes(self.addr1, 8)),
            bytes(read_ubytes(self.addr1 + 0x15, 8)),
            bytes(read_ubytes(self.addr2, 8)),
            bytes(read_ubytes(self.addr2 + 0xA, 8)),
        ]
        api.command.register(command, self.process_command)

    def _onunload(self):
        api.command.unregister(command)
        try:
            self.dispatch()
        except Exception:
            pass

    def is_patched(self):
        return read_ubytes(self.addr1, 8) == nop

    def patch(self):
        write_bytes(self.addr1, nop),
        write_bytes(self.addr1 + 0x15, nop),
        write_bytes(self.addr2, nop),
        write_bytes(self.addr2 + 0xA, nop),
        return "patch success"

    def dispatch(self):
        write_bytes(self.addr1, self.originals[0]),
        write_bytes(self.addr1 + 0x15, self.originals[1]),
        write_bytes(self.addr2, self.originals[2]),
        write_bytes(self.addr2 + 0xA, self.originals[3]),
        return "dispatch success"

    def process_command(self, args):
        api.Magic.echo_msg(self._process_command(args))

    def _process_command(self, arg):
        try:
            if len(arg):
                if arg[0] == "patch" or arg[0] == "p":
                    return self.patch()
                elif arg[0] == "dispatch" or arg[0] == "d":
                    return self.dispatch()
                else:
                    return "unknown arguments {}".format(arg[0])
            else:
                if self.is_patched():
                    return self.dispatch()
                else:
                    return self.patch()
        except Exception as e:
            return str(e)
