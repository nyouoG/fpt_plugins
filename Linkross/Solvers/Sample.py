from FFxivPythonTrigger.Logger import info
from ..Solver import SolverBase
from ..Game import card_type_sheet
from random import choice, sample, shuffle

types = {row['Name'] for row in card_type_sheet}


def try_choose(cards, limit=True):
    choose = list()
    cnt5 = 0
    cnt4 = 0
    if cards[5]:
        cnt5 = 1
        choose = [choice(cards[5])]
    if cards[4]:
        cnt4 = min(1 if limit else (2 - len(choose)), len(cards[4]))
        choose += sample(cards[4], cnt4)
    cnto = 0
    for i in range(3, 0, -1):
        if (cnto >= 3) if limit else (len(choose) >= 5): break
        l = min((3 - cnto) if limit else (5 - len(choose)), len(cards[i]))
        cnto += l
        choose += sample(cards[i], l)
    return choose, cnt5, cnt4


class SampleSolver(SolverBase):

    def suitable(self):
        return True

    def get_deck(self):
        cards = {i: list() for i in range(1, 6)}
        cardsT = {t: {i: list() for i in range(1, 6)} for t in types}
        same = 12 in self.current_rules
        dif = 13 in self.current_rules
        rev = 10 in self.current_rules
        need_type = same and not rev or dif and rev
        need_n_type = dif and not rev or same and rev
        for card in self.available_cards:
            cards[card.stars].append(card.card_id)
            cardsT[card.card_type][card.stars].append(card.card_id)
        choose, cnt5, cnt4 = list(), 0, 0
        if need_n_type:
            choose, cnt5, cnt4 = try_choose(cardsT[''])
        elif need_type:
            enemy_types = {card.card_type for card in self.card_event.fix_cards + self.card_event.variable_cards if card.card_type}
            order = [t for t in types if t and t not in enemy_types] + list(enemy_types)
            choose, cnt5, cnt4 = max([try_choose(cardsT[t]) for t in order], key=lambda x: len(x[0]))
        if len(choose) < 5:
            if cards[5] and not cnt5:
                cnt5 = 1
                choose += [choice(cards[5])]
            if len(choose) < 5:
                c4 = [card for card in cards[4] if card not in choose]
                if c4 and cnt4 + cnt5 < 2: choose += sample(c4, min(2 - cnt4 - cnt5, len(c4)))
            for i in range(3, 0, -1):
                if len(choose) >= 5: break
                c = [card for card in cards[i] if card not in choose]
                choose += sample(c, min(5 - len(choose), len(c)))
        shuffle(choose)
        return tuple(choose)

    def solve(self, game):
        hand_id = choice([i for i in range(5) if game.blue_cards[i] is not None] + [5])
        block_id = choice([i for i in range(9) if not game.blocks[i]] + [9])
        return hand_id, block_id
