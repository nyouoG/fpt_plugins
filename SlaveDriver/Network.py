from ctypes import *

from FFxivPythonTrigger import api

from FFxivPythonTrigger.memory.StructFactory import OffsetStruct

# cn5.55
ListReadyOpcode = 658
AdventureConfirmedOpcode = 958

# # cn5.5
# ListReadyOpcode = 282
# AdventureConfirmedOpcode = 514

# # cn5.45
# ListReadyOpcode = 262
# AdventureConfirmedOpcode = 842

# length
# ListReadyOpcode len:24
# AdventureConfirmedOpcode len:96

ClientEventStart = OffsetStruct({
    'target_id': c_uint,
    'unk0': c_uint,
    'event_id': c_ushort,
    'category': c_ushort,
    'unk3': c_uint,
}, 16)

ClientEventFinish = OffsetStruct({
    'event_id': c_ushort,
    'category': c_ushort,
    'unk2': c_uint,
    'unk3': c_uint,
    'unk4': c_uint,
}, 16)

ClientTrigger = OffsetStruct({
    'param1': c_uint,
    'param2': c_uint,
    'param3': c_uint,
    'param4': c_uint,
    'param5': c_uint,
    'param6': c_uint,
    'param7': c_uint,
    'param8': c_uint,
}, 32)

ask_list_trigger = ClientTrigger(param1=0x232c, param3=2, param6=0x40c66666)
confirm_retainer_hello_msg = ClientTrigger(param1=0x232c, param3=4, param6=0xac)
confirm_adventure_msg = ClientEventFinish(event_id=544, category=11, unk3=7, unk2=0x2000002)
finish_sending_adventure_msg = ClientEventFinish(event_id=544, category=11, unk2=3)
finish_sending_adventure_msg2 = ClientTrigger(param1=0x232c, param3=4, param6=0x7ff6)
finish_retainer_msg = ClientEventFinish(event_id=544, category=11, unk2=2)
close_list_msg = ClientEventFinish(event_id=544, category=11)


def is_start_list_response(evt):
    return evt.raw_msg.category == 11 and evt.raw_msg.event_id == 544


def start_list(target_id, bell_type):
    msg = ClientEventStart(target_id=target_id, event_id=544, category=11, unk0=bell_type)
    return api.XivNetwork.send_messages([("EventStart", bytearray(msg))], response_opcode="EventPlay", response_statement=is_start_list_response)


def ask_list():
    return api.XivNetwork.send_messages([("ClientTrigger", bytearray(ask_list_trigger))], response_opcode=ListReadyOpcode)


def start_retainer(retainer_id, server_id, is_continue=False):
    msg = ClientEventFinish(event_id=544, category=11, unk3=server_id, unk4=retainer_id, unk2=0x2000000 + int(is_continue))
    return api.XivNetwork.send_messages([("EventFinish", bytearray(msg))], response_opcode="EventPlay4")


def confirm_retainer_hello():
    api.XivNetwork.send_messages([("ClientTrigger", bytearray(confirm_retainer_hello_msg))])


def confirm_adventure():
    return api.XivNetwork.send_messages([("EventFinish", bytearray(confirm_adventure_msg))], response_opcode=AdventureConfirmedOpcode)


def resend_adventure(mission_id):
    msg = ClientTrigger(param1=0x12c, param2=mission_id, param6=0x7ff6)
    return api.XivNetwork.send_messages([("ClientTrigger", bytearray(msg))], response_opcode='Examine')


def confirm_retainer_go(mission_type):
    msg = ClientTrigger(param1=0x232c, param3=5, param4=mission_type)
    api.XivNetwork.send_messages([("ClientTrigger", bytearray(msg))])


def finish_sending_adventure():
    return api.XivNetwork.send_messages([("EventFinish", bytearray(finish_sending_adventure_msg))], response_opcode="EventPlay4")


def finish_sending_adventure2():
    return api.XivNetwork.send_messages([("ClientTrigger", bytearray(finish_sending_adventure_msg2))])


def finish_retainer():
    return api.XivNetwork.send_messages([("EventFinish", bytearray(finish_retainer_msg))], response_opcode="EventPlay",
                                        response_statement=is_start_list_response)


def close_list(is_work):
    msg = ClientEventFinish(event_id=544, category=11, unk2=int(is_work))
    api.XivNetwork.send_messages([("EventFinish", bytearray(msg))])
