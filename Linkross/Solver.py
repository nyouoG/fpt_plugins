from .Game import *


class SolverBase(object):
    def __init__(self, card_event: CardEvent, available_cards: list[Card], current_rules: set[int]):
        self.card_event = card_event
        self.available_cards = available_cards
        self.current_rules = current_rules

    def suitable(self) -> bool:
        """
        call when current rules are loaded
        :param current_rules: load rules
        :return: is this solver can be used
        """
        pass

    def get_deck(self) -> tuple[int, int, int, int, int]:
        """
        call when confirm joining the duel
        :return: deck formed, must be five card id
        """
        pass

    def solve(self, game: Game, force_hand: Optional[int]) -> tuple[int, int]:
        """
        call when its your round
        :param force_hand: the forced hand id in chaos
        :param game: the current game state
        :return: hand id of your card to use , block id to place
        """
        pass

    def end(self, game: Game):
        """
        call when game end
        :param game: pass
        """
        pass
