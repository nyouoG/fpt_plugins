import os
from time import sleep
from traceback import format_exc

from FFxivPythonTrigger import PluginBase
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import scan_address, scan_pattern, read_ushort
from FFxivPythonTrigger.Utils import wait_until

from .Networks import *
from .Game import *
from .Solver import SolverBase
from .Solvers import Sample,SolverA

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
    git_repo = 'nyouoG/fpt_plugins'
    repo_path = 'Linkross'
    hash_path = os.path.dirname(__file__)

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
                if self.card_event and read_ushort(a2 + 10) == 0x9:
                    talk_finish(read_ushort(a2 + 8))
                return r

        am = AddressManager(self.storage.data, self.logger)
        self.card_check_module = am.get('card_check_module', scan_address, card_check_module_sig, cmd_len=7)
        self._card_exist_func = card_exist_func(am.get('card_check_func', scan_pattern, card_check_func_sig))
        self.talk_hook = TalkHook(am.get('talk_hook', scan_address, talk_hook_sig, cmd_len=5))
        self.storage.save()
        self.register_event(f"network/recv/{recv_duel_desc_opcode}", self.init_rules)
        self.solvers = [SolverA.Solver]
        self.solver_used = None
        self.card_event = None
        self.available_cards = []
        self.auto_next = 0
        self.refresh_available_cards()
        api.command.register(command, self.process_command_entrance)

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
        data = recv_duel_desc_pack.from_buffer(event.raw_msg)
        if data.category != 0x23: return
        # self.logger(f"{self.card_event}\ncurrent rules: {','.join([rule_sheet[rule]['Name'] for rule in data.rules if rule])}")
        rules = set(data.rules)
        self.solver_used = None
        for solver_class in self.solvers:
            solver = solver_class(self.card_event, self.available_cards, rules)
            if solver.suitable():
                self.solver_used = solver
                return
        self.solver_used = "No Solver"

    def process_command_entrance(self, args):
        try:
            rtn = self.process_command(args)
            if rtn is not None: self.logger.debug(rtn)
        except:
            self.logger.error(format_exc())

    def _play_game(self, mode):
        target = api.XivMemory.targets.focus if mode == FOCUS else api.XivMemory.targets.current if mode == CURRENT else None
        if target is None: raise Exception(f"Unknown mode: {mode}")
        self.card_event = CardEvent.from_actor(target)
        event_id = self.card_event.event_id
        game_start(event_id, target.bNpcId)
        solver = wait_until(lambda: self.solver_used, timeout=0.5)
        if not isinstance(solver, SolverBase): raise Exception(f"No Solver Found")
        confirm_rule_1(event_id)
        confirm_rule_2(event_id)
        deck = solver.get_deck()
        self.logger(",".join([f"{card.card_id}:{card.name}[{card.card_type}]({card.stars})" for card in [Card.get_card(cid) for cid in deck]]))
        data = choose_cards(event_id, *deck)
        game = Game(BLUE if data.me_first else RED, data.my_card, data.enemy_card, data.rules[:])
        r_data = place_card(event_id, game.round, *(solver.solve(game, data.force_hand_id) if game.current_player == BLUE else []))
        game.place_card(r_data.block_id, r_data.hand_id, r_data.card_id)
        win = game.win()
        while win is None:
            #self.logger(game)
            if game.current_player == BLUE:
                choose=solver.solve(game, r_data.force_hand_id)
                #self.logger(choose)
                r_data = place_card(event_id, game.round, *choose)
            else:
                r_data = place_card(event_id, game.round)
            game.place_card(r_data.block_id, r_data.hand_id, r_data.card_id)
            win = game.win()
        self.logger("Blue win!" if win == BLUE else "Red win!" if win == RED else "Draw!")
        solver.end(game)
        end_game(event_id)
        game_finish(event_id)
        self.solver_used = None
        self.card_event = None

    def play_game(self, mode):
        self._play_game(mode)
        while self.auto_next:
            sleep(1)
            self._play_game(mode)

    def process_command(self, args):
        if args[0] == "[f]":
            self.create_mission(self.play_game, FOCUS)
        elif args[0] == "[c]":
            self.create_mission(self.play_game, CURRENT)
        elif args[0] == "auto_next":
            self.auto_next = int(not self.auto_next)
            return f"auto_next:{self.auto_next}"
