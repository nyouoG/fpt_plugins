from ..Solver import SolverBase
from ..Game import *
from random import choice, sample, shuffle

ALLOW_STEP: int = 20000


def available_action(event: CardEvent, game: Game, force_hand: int = None):
    ans = set()
    cards = list()
    unknown = None
    for hand_id, hand_card in enumerate(game.get_current_cards()):
        if hand_card is None or (force_hand is not None and hand_id != force_hand): continue
        if hand_card.is_unknown:
            unknown = hand_id
        else:
            cards.append((hand_id, hand_card.card.card_id))
    empty_block = [i for i in range(9) if game.blocks[i].card is None]
    red_card_onboard = {block.card.card_id for block in game.blocks if block.belongs_to_first == RED}
    red_card_onboard |= {h_c.card.card_id for h_c in game.red_cards if h_c is not None and not h_c.is_unknown}
    for hand_id, card_id in cards:
        for b_id in empty_block:
            ans.add((b_id, hand_id, card_id))
    if unknown is not None:
        for card in event.variable_cards + event.fix_cards:
            if card.card_id in red_card_onboard: continue
            for b_id in empty_block: ans.add((b_id, unknown, card.card_id))
    return list(ans)


def get_steps_score(event: CardEvent, game: Game, allow_try=None):
    win = game.win()
    if win is not None:
        if win == BLUE:
            return 1
        elif win == RED:
            return -1
        return -0.2
    actions = available_action(event, game, ((game.round + 1) // 2 if 8 in game.rules else None))
    if not actions: return 0
    if len(actions) > allow_try: actions = sample(actions, allow_try)
    each_allow = (allow_try - len(actions)) // len(actions) + 1
    # if allow_try > 1:info('',f'start {len(actions)}*{each_allow} try')
    games = map(lambda action: game.copy().place_card(*action), actions)
    scores = map(lambda _game: get_steps_score(event, _game, each_allow), games)
    return sum(scores) / len(actions)


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


cache_data = {}


class Solver(SolverBase):
    deck = None

    def suitable(self):
        return True

    def end(self, game: Game):
        if self.card_event.event_id not in cache_data:
            cache_data[self.card_event.event_id] = [self.deck, 0.5]
        if game.win() == RED:
            cache_data[self.card_event.event_id][1] -= 1
        elif game.win() == BLUE and cache_data[self.card_event.event_id][1] < 3:
            cache_data[self.card_event.event_id][1] += 1
        else:
            cache_data[self.card_event.event_id][1] -= 0.5

    def get_deck(self):
        if self.card_event.event_id in cache_data:
            deck, score = cache_data[self.card_event.event_id]
            if score < 0:
                del cache_data[self.card_event.event_id]
            else:
                return deck
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
        self.deck = tuple(choose)
        return self.deck

    def solve(self, game, force_hand):
        actions = available_action(self.card_event, game, force_hand)
        # info('', actions)
        each_allow = None if ALLOW_STEP is None else ALLOW_STEP // len(actions)
        games = map(lambda action: (action, game.copy().place_card(*action)), actions)
        scores = map(lambda _game: (_game[0], get_steps_score(self.card_event, _game[1], each_allow)), games)
        b_id, h_id, c_id = max(scores, key=lambda x: x[1])[0]
        return h_id, b_id
