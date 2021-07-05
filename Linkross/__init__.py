from threading import Lock
from time import sleep
from traceback import format_exc

from FFxivPythonTrigger import PluginBase, api
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_address, scan_pattern, read_ushort, read_uint

from .Networks import *
from .Game import *
from .Solver import SolverBase
from .Solvers import Sample

command = "@Linkross"

card_exist_func = CFUNCTYPE(c_ubyte, c_uint64, c_ushort)

card_check_func_sig = "40 53 48 83 EC ? 48 8B D9 66 85 D2 74 ?"
card_check_module_sig = "48 8D 0D ? ? ? ? 89 7C 24 ? 8D 57 ?"
talk_hook_sig = "E8 ? ? ? ? 4C 8B 75 ? 4D 3B FE"

FOCUS = 1
CURRENT = 2

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

        class TalkHook(Hook):
            restype = c_uint64
            argtypes = [c_uint64, c_uint64]

            def hook_function(_self, a1, a2):
                r = _self.original(a1, a2)
                if self.stage and read_ushort(a2 + 10) == 0x9:
                    talk_finish(read_ushort(a2 + 8))
                return r

        am = AddressManager(self.storage.data, self.logger)
        self.card_check_module = am.get('card_check_module', scan_address, card_check_module_sig, cmd_len=7)
        self._card_exist_func = card_exist_func(am.get('card_check_func', scan_pattern, card_check_func_sig))
        self.talk_hook = TalkHook(am.get('talk_hook', scan_address, talk_hook_sig, cmd_len=5))
        self.storage.save()
        self.register_event(f"network/recv/{recv_game_data_opcode}", self.start_game)
        self.register_event(f"network/recv/{recv_place_card_opcode}", self.place_card)
        self.register_event(f"network/recv/{recv_duel_desc_opcode}", self.init_rules)
        self.register_event(f"network/recv/{recv_duel_action_finish_opcode}", self.duel_next_step)
        self.register_event(f"network/recv_event_finish", self.reset)
        self.solvers = [Sample.SampleSolver]
        self.solver_used = None
        self.game = None
        self.card_event = None
        self.stage = 0
        self.available_cards = []
        self.auto_next = False
        self.mode = FOCUS
        self.lock = Lock()
        self.refresh_available_cards()
        api.command.register(command, self.process_command_entrance)

    def reset(self, event):
        if event.raw_msg.category == 0x23:
            self.logger("reset!")
            self.solver_used = None
            self.game = None
            self.card_event = None
            self.stage = 0
            if self.auto_next:
                self.start_new()

    def refresh_available_cards(self):
        self.available_cards = [Card(row.key) for row in card_sheet if row.key and self.card_exist(row.key)]
        self.logger(f"load {len(self.available_cards)} available cards:\n{','.join(map(str, self.available_cards))}")

    def card_exist(self, card_id: int):
        return bool(self._card_exist_func(self.card_check_module, card_id))

    def _start(self):
        self.talk_hook.install()
        self.talk_hook.enable()

    def _onunload(self):
        api.command.unregister(command)
        self.talk_hook.uninstall()

    def init_rules(self, event):
        with self.lock:
            data = recv_duel_desc_pack.from_buffer(event.raw_msg)
            if data.category != 0x23 or self.stage != CONFIRM_TALK: return
            self.stage += 0.5
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
        with self.lock:
            if self.stage == CONFIRM_RULE:
                if self.solver_used is None: return
                confirm_rule_1(self.card_event.event_id)
                self.stage += 1
            elif self.stage == CONFIRM_RULE + 1:
                confirm_rule_2(self.card_event.event_id)
                self.stage += 1
            elif self.stage == CONFIRM_DECK:
                deck = self.solver_used.get_deck()
                self.logger(deck)
                choose_cards(self.card_event.event_id, *deck)
                self.stage += 1

    def start_game(self, event):
        data = recv_game_data_pack.from_buffer(event.raw_msg)
        if data.category != 35: return
        self.game = Game(BLUE if data.me_first else RED, data.my_card, data.enemy_card, data.rules[:])
        #self.logger(self.game)
        if not self.stage: return
        if data.me_first:
            place_card(self.card_event.event_id, self.game.round, *self.solver_used.solve(self.game))
        else:
            place_card(self.card_event.event_id, self.game.round)

    def place_card(self, event):
        data = recv_place_card_pack.from_buffer(event.raw_msg)
        if data.category != 35 : return
        if self.game is not None:
            self.game.place_card(data.block_id, data.hand_id, data.card_id)
            #self.logger(self.game)
            win = self.game.win()
            if win is not None:
                if win == BLUE:
                    self.logger("Blue win!")
                elif win == RED:
                    self.logger("Red win!")
                else:
                    self.logger("Draw!")
                self.game = None
                if self.stage > CONFIRM_DECK:
                    end_game(self.card_event.event_id)
                    game_finish(self.card_event.event_id)
            elif self.game.current_player == BLUE and self.stage > CONFIRM_DECK:
                place_card(self.card_event.event_id, self.game.round, *self.solver_used.solve(self.game))
            elif self.game.current_player == RED and self.stage > CONFIRM_DECK:
                place_card(self.card_event.event_id, self.game.round)

    def start_new(self):
        if self.stage:
            raise Exception(f"current stage: {self.stage}")
        if self.mode == FOCUS:
            target = api.XivMemory.targets.focus
        elif self.mode == CURRENT:
            target = api.XivMemory.targets.current
        else:
            raise Exception(f"Unknown mode: {self.mode}")
        self.card_event = CardEvent.from_actor(target)
        game_start(self.card_event.event_id, target.bNpcId)
        self.stage = CONFIRM_TALK

    def process_command_entrance(self, args):
        try:
            rtn = self.process_command(args)
            if rtn is not None: self.logger.debug(rtn)
        except:
            self.logger.error(format_exc())

    def process_command(self, args):
        if args[0] == "[f]":
            self.mode = FOCUS
            self.start_new()
        elif args[0] == "[c]":
            self.mode = CURRENT
            self.start_new()
        elif args[0] == "auto_next":
            self.auto_next = not self.auto_next
            return f"auto_next:{self.auto_next}"
