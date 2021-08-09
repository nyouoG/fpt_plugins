import time
from ctypes import *
from functools import cache

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from . import Network

command = "@slave"

bell_name = "传唤铃"

AdventureData = OffsetStruct({
    'mission_id': (c_uint, 0),
    'next_mission_id': (c_uint, 0x1c),
    'mission_type': (c_uint, 0x28),
})

mission_sheet = realm.game_data.get_sheet('RetainerTask')

DEFAULT_MISSION = 395


def find_bell_id():
    me = api.XivMemory.actor_table.get_me()
    for actor in api.XivMemory.actor_table.get_actors_by_name(bell_name):
        if me.absolute_distance_xy(actor) < 5:
            if actor.type == 12:
                return actor.id, 0
            if actor.type == 7:
                return actor.bNpcId, 1
    raise Exception("No bell found")


@cache
def mission_name(mission_id):
    return mission_sheet[mission_id]['Task']['Name']


class SlaveDriver(PluginBase):
    name = "SlaveDriver"

    def __init__(self):
        super().__init__()
        self.working = False
        self.retainers = dict()
        self.register_event("network/recv_retainer_info", self.recv_retainer_info)
        api.XivNetwork.register_makeup("EventFinish", self.def_finish)
        api.XivNetwork.register_makeup("ClientTrigger", self.def_trigger)
        api.command.register(command, self.process_command)

    def _start(self):
        # self.start_mission()
        pass

    def _onunload(self):
        api.XivNetwork.unregister_makeup("EventFinish", self.def_finish)
        api.XivNetwork.unregister_makeup("ClientTrigger", self.def_trigger)
        api.command.unregister(command)

    def recv_retainer_info(self, event):
        msg = event.raw_msg
        if not msg.reserved: return
        self.retainers[msg.name] = msg

    def def_finish(self, header, raw):
        return header, bytearray(Network.ClientEventFinish()) if self.working else raw

    def def_trigger(self, header, raw):
        return header, bytearray(Network.ClientTrigger()) if self.working else raw

    def process_command(self, args):
        if args[0] == "open":
            Network.start_list(api.XivMemory.actor_table.get_me().id, 0)
        elif args[0] == "collect":
            self.start_mission()
        elif args[0] == "close":
            Network.close_list(1)

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

        current = time.time()

        retainers_process = []
        for name, msg in self.retainers.items():
            if msg.adv_end_time:
                if msg.adv_end_time <= current:
                    retainers_process.append((msg.retainer_id, msg.server_id, name, True))
                    status = f"{mission_name(msg.mission_id)} finished"
                else:
                    dif = msg.adv_end_time - current
                    status = f"{mission_name(msg.mission_id)} finish after {dif // 3600:.0f}h {dif % 3600 // 60:.0f}m {dif % 60:.0f}s"
            else:
                status = f"no mission"
                retainers_process.append((msg.retainer_id, msg.server_id, name, False))
            self.logger(f"{name}: {status}")
        self.logger(f"{len(retainers_process)} retainers need process")

        cnt = 0
        while retainers_process:
            retainer_id, server_id, name, is_adv = retainers_process.pop()
            if not is_adv:
                continue
            self.logger(f"process retainer {name}")
            Network.start_retainer(retainer_id, server_id, bool(cnt))
            Network.confirm_retainer_hello()
            if is_adv:
                res = Network.confirm_adventure()
                data = AdventureData.from_buffer(res.raw_msg)
                mission_id = data.next_mission_id
                mission_type = data.mission_type
            else:
                res = Network.confirm_adventure()
                mission_id = AdventureData.from_buffer(res.raw_msg).next_mission_id
                mission_type = DEFAULT_MISSION
            self.logger(f"send mission: {mission_name(mission_type)}")
            Network.resend_adventure(mission_id)
            Network.confirm_retainer_go(mission_type)
            Network.finish_sending_adventure()
            Network.finish_sending_adventure2()
            Network.finish_retainer()
            Network.ask_list()
            cnt += 1
            time.sleep(0.05)
        Network.close_list(bool(cnt))
