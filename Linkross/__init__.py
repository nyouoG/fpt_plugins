from time import sleep
from traceback import format_exc

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.memory import scan_address, scan_pattern

from .Networks import *
from .Game import *
from .Solver import SolverBase
from .Solvers import Sample

command = "@Linkross"

card_exist_func = CFUNCTYPE(c_ubyte, c_uint64, c_ushort)

card_check_func_sig = "40 53 48 83 EC ? 48 8B D9 66 85 D2 74 ?"
card_check_module_sig = "48 8D 0D ? ? ? ? 89 7C 24 ? 8D 57 ?"

FOCUS = 1
CURRENT = 2

START = 10
CONFIRM_TALK = 11
CONFIRM_RULE = 12
CONFIRM_DECK = 14
DUEL = 15


class Linkross(PluginBase):
    name = "Linkross"
    game: Optional[Game]
    card_event: Optional[CardEvent]
    available_cards: list[Card]
    solvers: list[Type[SolverBase]]
    solver_used: Optional[SolverBase]

    def __init__(self):
        super().__init__()
        am = AddressManager(self.storage.data, self.logger)
        self.card_check_module = am.get('card_check_module', scan_address, card_check_module_sig, cmd_len=7)
        self._card_exist_func = card_exist_func(am.get('card_check_func', scan_pattern, card_check_func_sig))
        self.storage.save()
        self.register_event(f"network/recv/{recv_game_data_opcode}", self.start_game)
        self.register_event(f"network/recv/{recv_place_card_opcode}", self.place_card)
        self.register_event(f"network/recv/{recv_duel_desc_opcode}", self.init_rules)
        self.register_event(f"network/recv/{recv_duel_action_finish_opcode}", self.duel_next_step)
        self.register_event(f"network/recv_event_play", self.finish_talk)
        self.register_event(f"network/recv_event_finish", self.reset)
        self.solvers = [Sample.SampleSolver]
        self.solver_used = None
        self.game = None
        self.card_event = None
        self.stage = 0
        self.available_cards = []
        self.refresh_available_cards()
        api.command.register(command, self.process_command_entrance)

    def reset(self, event):
        if event.raw_msg.category == 0x23:
            self.solver_used = None
            self.game = None
            self.card_event = None
            self.stage = 0

    def refresh_available_cards(self):
        self.available_cards = [Card(row.key) for row in card_sheet if row.key and self.card_exist(row.key)]
        self.logger(f"load {len(self.available_cards)} available cards:\n{','.join(map(str, self.available_cards))}")

    def card_exist(self, card_id: int):
        return bool(self._card_exist_func(self.card_check_module, card_id))

    def _onunload(self):
        api.command.unregister(command)

    def init_rules(self, event):
        data = recv_duel_desc_pack.from_buffer(event.raw_msg)
        if data.category != 0x23 or self.stage != CONFIRM_TALK: return
        self.logger(f"{self.card_event}\ncurrent rules: {','.join([rule_sheet[rule]['Name'] for rule in data.rules if rule])}")
        rules = set(data.rules)
        self.solver_used = None
        for solver_class in self.solvers:
            solver = solver_class(self.card_event, self.available_cards)
            if solver.suitable(rules):
                self.solver_used = solver
                break
        self.stage = CONFIRM_RULE

    def duel_next_step(self, event):
        if not self.stage: return
        while self.stage <= CONFIRM_TALK:
            sleep(0.01)
        if self.stage == CONFIRM_RULE:
            if self.solver_used is None: return
            continue_msg = send_event_action(category=0x23, event_id=self.card_event.event_id, param3=2, param4=2)
            continue_msg.param8 = 1
            api.XivNetwork.send_messages([("EventAction", bytearray(continue_msg))])
            self.stage += 1
        elif self.stage == CONFIRM_RULE + 1:
            continue_msg = send_event_action(category=0x23, event_id=self.card_event.event_id, param3=1, param4=3)
            continue_msg.param8 = 51
            continue_msg.param9 = 2
            api.XivNetwork.send_messages([("EventAction", bytearray(continue_msg))])
            self.stage += 1
        elif self.stage == CONFIRM_DECK:
            deck=self.solver_used.get_deck()
            self.logger(deck)
            deck_choose = send_card_choose_pack(category=0x23, event_id=self.card_event.event_id, cards=deck)
            api.XivNetwork.send_messages([(send_card_choose_opcode, bytearray(deck_choose))])
            self.stage += 1

    def start_game(self, event):
        data = recv_game_data_pack.from_buffer(event.raw_msg)
        if data.category != 35: return
        self.game = Game(BLUE if data.me_first else RED, data.my_card, data.enemy_card, data.rules[:])
        self.logger(self.game)
        if data.me_first:
            hand_id, block_id = self.solver_used.solve(self.game)
            self.logger(f"hand: {hand_id}, block: {block_id}")
            send_msg = send_place_card_pack(category=0x23,
                                            event_id=self.card_event.event_id,
                                            round=self.game.round,
                                            hand_id=hand_id, block_id=block_id)
            api.XivNetwork.send_messages([(send_place_card_opcode, bytearray(send_msg))])
        else:
            send_msg = send_place_card_pack(category=0x23,
                                            event_id=self.card_event.event_id,
                                            round=self.game.round,
                                            hand_id=5, block_id=9)
            api.XivNetwork.send_messages([(send_place_card_opcode, bytearray(send_msg))])

    def place_card(self, event):
        data = recv_place_card_pack.from_buffer(event.raw_msg)
        if data.category != 35: return
        if self.game is not None and self.stage > CONFIRM_DECK:
            self.game.place_card(data.block_id, data.hand_id, data.card_id)
            self.logger(self.game)
            win = self.game.win()
            if win is not None:
                if win == BLUE:
                    self.logger("Blue win!")
                elif win == RED:
                    self.logger("Red win!")
                else:
                    self.logger("Draw!")
                self.game = None
                finish_massage = send_event_action(category=0x23, event_id=self.card_event.event_id, param3=1, param4=6)
                finish_massage.param8 = 189
                api.XivNetwork.send_messages([("EventAction", bytearray(finish_massage))])
                # msg = send_event_finish(category=0x23, event_id=self.card_event.event_id)
                # api.XivNetwork.send_messages([("EventFinish", bytearray(msg))])
            elif self.game.current_player == BLUE:
                hand_id, block_id = self.solver_used.solve(self.game)
                self.logger(f"hand: {hand_id}, block: {block_id}")
                send_msg = send_place_card_pack(category=0x23,
                                                event_id=self.card_event.event_id,
                                                round=self.game.round,
                                                hand_id=hand_id,block_id=block_id)
                api.XivNetwork.send_messages([(send_place_card_opcode, bytearray(send_msg))])
            elif self.game.current_player == RED:
                send_msg = send_place_card_pack(category=0x23,
                                                event_id=self.card_event.event_id,
                                                round=self.game.round,
                                                hand_id=5,block_id=9)
                api.XivNetwork.send_messages([(send_place_card_opcode, bytearray(send_msg))])

    def start_new(self, mode: int):
        if self.stage:
            raise Exception(f"current stage: {self.stage}")
        if mode == FOCUS:
            target = api.XivMemory.targets.focus
        elif mode == CURRENT:
            target = api.XivMemory.targets.current
        else:
            raise Exception(f"Unknown mode: {mode}")
        self.card_event = CardEvent.from_actor(target)
        self.stage = START
        msg = send_client_trigger(category=0x23, event_id=self.card_event.event_id, target_bnpc_id=target.bNpcId, unk0=0x32f, unk1=0x1)
        api.XivNetwork.send_messages([("ClientTrigger", bytearray(msg))])

    def finish_talk(self, event):
        if self.stage == START and event.raw_msg.category == 0x9:
            msg = send_event_finish(category=0x9, event_id=event.raw_msg.event_id)
            api.XivNetwork.send_messages([("EventFinish", bytearray(msg))])
            self.stage = CONFIRM_TALK

    def process_command_entrance(self, args):
        try:
            rtn = self.process_command(args)
            if rtn is not None: self.logger.debug(rtn)
        except:
            self.logger.error(format_exc())

    def process_command(self, args):
        if args[0] == "[f]":
            self.start_new(FOCUS)
        elif args[0] == "[c]":
            self.start_new(CURRENT)
