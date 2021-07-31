import time
from ctypes import *

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from . import Network
command = "@slave"

bell_name = "传唤铃"

AdventureData = OffsetStruct({
    'mission_id': (c_uint, 0),
    'next_mission_id': (c_uint, 0x1c),
    'mission_type': (c_uint, 0x28),
})


def find_bell_id():
    me = api.XivMemory.actor_table.get_me()
    for actor in api.XivMemory.actor_table.get_actors_by_name(bell_name):
        if me.absolute_distance_xy(actor) < 5:
            if actor.type == 12:
                return actor.id, 0
            if actor.type == 7:
                return actor.bNpcId, 1
    raise Exception("No bell found")


class SlaveDriver(PluginBase):
    name = "SlaveDriver"

    def __init__(self):
        super().__init__()
        self.working = False
        self.retainers_finished = set()
        self.register_event("network/recv_retainer_info", self.recv_retainer_info)
        api.XivNetwork.register_makeup("EventFinish", self.def_finish)
        api.XivNetwork.register_makeup("ClientTrigger", self.def_trigger)
        api.command.register(command, self.process_command)

    def _start(self):
        #self.start_mission()
        pass

    def _onunload(self):
        api.XivNetwork.unregister_makeup("EventFinish", self.def_finish)
        api.XivNetwork.unregister_makeup("ClientTrigger", self.def_trigger)
        api.command.unregister(command)

    def recv_retainer_info(self, event):
        msg = event.raw_msg
        if not msg.reserved: return
        retainer = (msg.retainer_id, msg.server_id)
        if msg.adv_end_time and msg.adv_end_time < time.time():
            self.retainers_finished.add(retainer)
        else:
            if retainer in self.retainers_finished:
                self.retainers_finished.remove(retainer)

    def def_finish(self, header, raw):
        return header, bytearray(Network.ClientEventFinish()) if self.working else raw

    def def_trigger(self, header, raw):
        return header, bytearray(Network.ClientTrigger()) if self.working else raw

    def process_command(self, args):
        if args[0] == "open":
            Network.start_list(api.XivMemory.actor_table.get_me().id, 0)
        elif args[0] == "collect":
            self.start_mission()

    def start_mission(self):
        self.working = True
        try:
            self._start_mission()
        finally:
            self.working = False

    def _start_mission(self):
        Network.start_list(api.XivMemory.actor_table.get_me().id, 0)
        Network.ask_list()
        time.sleep(0.05)
        cnt = 0
        while self.retainers_finished:
            self.logger(self.retainers_finished)
            retainer_id, server_id = self.retainers_finished.pop()
            Network.start_retainer(retainer_id, server_id, bool(cnt))
            Network.confirm_retainer_hello()
            res = Network.confirm_adventure()
            data = AdventureData.from_buffer(res.raw_msg)
            Network.resend_adventure(data.next_mission_id)
            Network.confirm_retainer_go(data.mission_type)
            Network.finish_sending_adventure()
            Network.finish_sending_adventure2()
            Network.finish_retainer()
            Network.ask_list()
            cnt += 1
            time.sleep(0.05)
        Network.close_list(bool(cnt))
