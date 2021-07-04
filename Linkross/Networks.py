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
    'round': (c_uint, 0xc),
    'hand_id': (c_uint, 0x10),
    'block_id': (c_uint, 0x14),
}, 24)

send_card_choose_pack = OffsetStruct({
    'event_id': (c_ushort, 0x0),
    'category': (c_ushort, 0x2),
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

send_event_action=OffsetStruct({
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

