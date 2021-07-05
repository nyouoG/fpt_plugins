from FFxivPythonTrigger import api
from FFxivPythonTrigger.memory.StructFactory import *

send_place_card_opcode = 246
send_card_choose_opcode = 512
recv_place_card_opcode = 225
recv_duel_action_finish_opcode = 714
recv_duel_desc_opcode = 259
recv_game_data_opcode = 822

send_place_card_pack = OffsetStruct({
    'event_id': (c_ushort, 0x0),
    'category': (c_ushort, 0x2),
    'unk0':(c_uint,0x4),
    'unk1':(c_uint,0x8),
    'round': (c_uint, 0xc),
    'hand_id': (c_uint, 0x10),
    'block_id': (c_uint, 0x14),
}, 24)

send_card_choose_pack = OffsetStruct({
    'event_id': (c_ushort, 0x0),
    'category': (c_ushort, 0x2),
    'unk0': (c_uint, 0x4),
    'unk1': (c_uint, 0x8),
    'cards': (c_uint * 5, 0xc),
}, 40)

send_client_trigger = OffsetStruct({
    'unk0': (c_uint, 0),
    'event_id': (c_ushort, 0x4),
    'category': (c_ushort, 0x6),
    'target_bnpc_id': (c_uint, 0x18),
    'unk1': (c_uint, 0x1c),
})

send_event_finish = OffsetStruct({
    'event_id': c_ushort,
    'category': c_ushort,
    'unk2': c_uint,
    'unk3': c_uint,
    'unk4': c_uint,
}, 16)

send_event_action = OffsetStruct({
    'event_id': c_ushort,
    'category': c_ushort,
    'param0': c_ubyte,
    'param1': c_ubyte,
    'param2': c_ubyte,
    'param3': c_ubyte,
    'param4': c_ubyte,
    'param5': c_ubyte,
    'param6': c_ubyte,
    'param7': c_ubyte,
    'param8': c_ubyte,
    'param9': c_ubyte,
    'param10': c_ubyte,
    'param11': c_ubyte,
}, 16)

recv_place_card_pack = OffsetStruct({
    'event_id': (c_ushort, 0x0),
    'category': (c_ushort, 0x2),
    'block_id': (c_ubyte, 0xc),
    'hand_id': (c_ubyte, 0xd),
    'card_id': (c_ushort, 0xe),
}, 24)

recv_duel_action_finish_pack = OffsetStruct({
    'event_id': (c_ushort, 0x0),
    'category': (c_ushort, 0x2),
}, 16)

recv_duel_desc_pack = OffsetStruct({
    'event_id': (c_ushort, 0x0),
    'category': (c_ushort, 0x2),
    'rules': (c_ubyte * 4, 0xc),
}, 40)


class recv_game_data_pack(OffsetStruct({
    'event_id': (c_ushort, 0x0),
    'category': (c_ushort, 0x2),
    'rules': (c_ubyte * 4, 0xc),
    'first': (c_ubyte, 0x13),
    'cards': (c_ushort * 10, 0x18),
}, 72, ['my_card', 'enemy_card', 'me_first'])):
    @property
    def me_first(self):
        return self.first == 1

    @property
    def my_card(self):
        return [self.cards[1], self.cards[0], self.cards[3], self.cards[2], self.cards[5]]

    @property
    def enemy_card(self):
        return [self.cards[4], self.cards[7], self.cards[6], self.cards[9], self.cards[8]]


def game_start(event_id, b_npc_id):
    msg = send_client_trigger(category=0x23, event_id=event_id, target_bnpc_id=b_npc_id, unk0=0x32f, unk1=0x1)
    api.XivNetwork.send_messages([("ClientTrigger", bytearray(msg))])


def end_game(event_id):
    finish_massage = send_event_action(category=0x23, event_id=event_id, param3=1, param4=6)
    finish_massage.param8 = 189
    api.XivNetwork.send_messages([("EventAction", bytearray(finish_massage))])

def talk_finish(event_id):
    msg = send_event_finish(category=0x9, event_id=event_id)
    api.XivNetwork.send_messages([("EventFinish", bytearray(msg))])


def game_finish(event_id):
    msg = send_event_finish(category=0x23, event_id=event_id)
    api.XivNetwork.send_messages([("EventFinish", bytearray(msg))])


def place_card(event_id, game_round, hand_id=5, block_id=9):
    msg = send_place_card_pack(category=0x23, event_id=event_id, round=game_round, hand_id=hand_id, block_id=block_id)
    msg.unk0=0x4000000
    msg.unk1=0x5
    api.XivNetwork.send_messages([(send_place_card_opcode, bytearray(msg))])


def choose_cards(event_id, card1, card2, card3, card4, card5):
    deck_choose = send_card_choose_pack(category=0x23, event_id=event_id, cards=(card1, card2, card3, card4, card5))
    deck_choose.unk0 = 0x6000000
    deck_choose.unk1 = 0x4
    api.XivNetwork.send_messages([(send_card_choose_opcode, bytearray(deck_choose))])


def confirm_rule_1(event_id):
    continue_msg = send_event_action(category=0x23, event_id=event_id, param3=2, param4=2)
    continue_msg.param8 = 1
    api.XivNetwork.send_messages([("EventAction", bytearray(continue_msg))])


def confirm_rule_2(event_id):
    continue_msg = send_event_action(category=0x23, event_id=event_id, param3=1, param4=3)
    continue_msg.param8 = 51
    continue_msg.param9 = 2
    api.XivNetwork.send_messages([("EventAction", bytearray(continue_msg))])
