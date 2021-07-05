from FFxivPythonTrigger.Logger import info
from ..Solver import SolverBase
from random import choice, sample, shuffle


class SampleSolver(SolverBase):
    def suitable(self, current_rules):
        return True

    def get_deck(self):
        cards = {i: list() for i in range(1, 6)}
        for card in self.available_cards:
            cards[card.stars].append(card.card_id)
        choose = list()
        if cards[5]:
            choose.append(choice(cards[5]))
        elif cards[4]:
            choose.append(choice(cards[4]))
        for i in range(3, 0, -1):
            if len(choose) >= 5: break
            choose += sample(cards[i], min(5 - len(choose), len(cards[i])))
        shuffle(choose)
        return tuple(choose)

    def solve(self, game):
        hand_id = 5
        for i in range(5):
            if game.get_current_cards()[i] is not None:
                hand_id = i
                break
        block_id = 9
        for i in range(9):
            if not game.blocks[i]:
                block_id = i
                break
        #info('',hand_id,block_id)
        return hand_id, block_id
