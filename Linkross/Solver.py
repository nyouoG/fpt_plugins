from .Game import *


class SolverBase(object):
    def __init__(self, card_event: CardEvent, available_cards: list[Card]):
        self.card_event = card_event
        self.available_cards = available_cards

    def suitable(self, current_rules: set[int]) -> bool:
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

    def solve(self,game:Game)->tuple[int,int]:
        """
        call when its your round
        :param game: the current game state
        :return: hand id of your card to use , block id to place
        """
        pass
