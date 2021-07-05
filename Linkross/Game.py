from functools import cached_property, cache
from typing import Optional
from copy import deepcopy

from FFxivPythonTrigger.SaintCoinach import realm


"""
1	天选	出现什么规则完全交给命运女神来决定。
2	全明牌	互相公开手中所有的卡片进行游戏。
3	三明牌	互相随机公开手中三张卡片进行游戏。
4	同数	使出的卡片如果2边以上（含2边）的数值均与相邻的卡片数值相等，则会取得相邻卡片的控制权。
5	不胜不休	出现平局时会以场上双方各自控制的卡片重新开始对局。
6	加算	使出的卡片如果2边以上（含2边）的数值各自与相邻的卡片对应数值相加的和相等，则会取得相邻卡片的控制权。
7	随机	各自从手中所有卡片中随机抽出5张卡进行对局。
8	秩序	双方必须按照卡组中卡片的位置顺序使用卡片。
9	混乱	双方必须按照随机决定的顺序使用卡片。
10	逆转	逆转卡片的强度。
11	王牌杀手	A会被1所控制。逆转规则下1会被A所控制。
12	同类强化	带有类型的卡片会随场上设置的同一类型卡片的数量增多而变强。
13	同类弱化	带有类型的卡片会随场上设置的同一类型卡片的数量增多而变弱。
14	交换	双方随机从自己的卡组中抽出一张卡与对方交换。
15	选拔	以随机分配到的卡片组成卡组进行对战。
"""

card_sheet = realm.game_data.get_sheet('TripleTriadCardResident')
card_desc_sheet = realm.game_data.get_sheet('TripleTriadCard')
rule_sheet = realm.game_data.get_sheet('TripleTriadRule')
enpc_sheet = realm.game_data.get_sheet('ENpcBase')
card_event_sheet = realm.game_data.get_sheet("TripleTriad")

MAX_CARD_ID = 316

NONE = 0
BLUE = 1
RED = -1
TOP = 2
BOTTOM = -2
LEFT = 3
RIGHT = -3

directions = [TOP, BOTTOM, LEFT, RIGHT]


class CardEvent(object):
    def __init__(self, row):
        self._row = row
        self.event_id = row.key & 0xffff

    @cached_property
    def fix_cards(self):
        cards = list()
        for i in range(5):
            card = self._row["TripleTriadCard{Fixed}[%s]" % i].key
            if card:
                cards.append(Card.get_card(card))
            else:
                break
        return cards

    @cached_property
    def variable_cards(self):
        cards = list()
        for i in range(5):
            card = self._row["TripleTriadCard{Variable}[%s]" % i].key
            if card:
                cards.append(Card.get_card(card))
            else:
                break
        return cards

    @cached_property
    def rewards(self):
        rewards = list()
        for i in range(4):
            reward = self._row["Item{PossibleReward}[%s]" % i]
            if reward is None:
                break
            else:
                rewards.append(reward)
        return rewards

    @cached_property
    def rules(self):
        rules = set()
        for i in range(2):
            rule = self._row["TripleTriadRule[%s]" % i]
            if rule is None:
                break
            else:
                rules.add(rule.key)
        return rules

    @cached_property
    def use_regon(self):
        return self._row["UsesRegionalRules"]

    @classmethod
    @cache
    def from_actor(cls, actor):
        if not actor.eNpcId: raise Exception("Actor is not an Enpc")
        enpc = enpc_sheet[actor.eNpcId]
        for i in range(32):
            evt = enpc[f"ENpcData[{i}]"]
            if evt is None: break
            if evt.sheet.name == "TripleTriad": return cls(evt)
        raise Exception("target actor has no card event")

    @classmethod
    @cache
    def from_event_id(cls, event_id):
        return cls(card_event_sheet[event_id | 0x230000])

    def __str__(self):
        return f"card event {self.event_id}\n" \
               f"fix: {','.join(map(str, self.fix_cards))}\n" \
               f"var: {','.join(map(str, self.variable_cards))}\n" \
               f"rules: {','.join([rule_sheet[rule]['Name'] for rule in self.rules])}\n" \
               f"use_regon: {self.use_regon}"

    def __hash__(self):
        return self.event_id

    def __eq__(self, other):
        if type(other) == CardEvent:
            return self.event_id == other.event_id
        else:
            return self.event_id == other

    @cached_property
    def win_talk_id(self):
        return self._row["DefaultTalk{PCWin}"].key

    @cached_property
    def draw_talk_id(self):
        return self._row["DefaultTalk{Draw}"].key

    @cached_property
    def lose_talk_id(self):
        return self._row["DefaultTalk{NPCWin}"].key

class Card(object):
    def __init__(self, card_id: int):
        self.card_id = card_id
        self._card = card_sheet[card_id]
        self._desc = card_desc_sheet[card_id]

    def __hash__(self):
        return self.card_id

    def __eq__(self, other):
        if type(other) == Card:
            return self.card_id == other.card_id
        else:
            return self.card_id == other

    def __str__(self):
        return self.name

    @cached_property
    def name(self):
        return self._desc['Name']

    @cached_property
    def top(self):
        return self._card["Top"]

    @cached_property
    def bottom(self):
        return self._card["Bottom"]

    @cached_property
    def left(self):
        return self._card["Left"]

    @cached_property
    def right(self):
        return self._card["Right"]

    @cached_property
    def card_type(self):
        return self._card["TripleTriadCardType"]["Name"]

    @cached_property
    def stars(self):
        return self._card["TripleTriadCardRarity"]["Stars"]

    def get(self, direction: int):
        if direction == TOP:
            return self.top
        elif direction == BOTTOM:
            return self.bottom
        elif direction == LEFT:
            return self.left
        elif direction == RIGHT:
            return self.right

    @classmethod
    @cache
    def get_card(cls, card_id):
        return cls(card_id)


class Block(object):
    def __init__(self, game: 'Game', block_id: int):
        self.block_id = block_id
        self.game = game
        self.card: Optional[Card] = None
        self.belongs_to = 0


    def copy(self):
        return deepcopy(self)

    @property
    def has_top(self):
        return self.block_id > 2

    @property
    def has_bottom(self):
        return self.block_id < 6

    @property
    def has_left(self):
        return self.block_id % 3 > 0

    @property
    def has_right(self):
        return self.block_id % 3 < 2

    @property
    def top(self):
        if self.has_top: return self.game.blocks[self.block_id - 3]

    @property
    def bottom(self):
        if self.has_bottom: return self.game.blocks[self.block_id + 3]

    @property
    def left(self):
        if self.has_left: return self.game.blocks[self.block_id - 1]

    @property
    def right(self):
        if self.has_right: return self.game.blocks[self.block_id + 1]

    def get(self, direction: int):
        if direction == TOP:
            return self.top
        elif direction == BOTTOM:
            return self.bottom
        elif direction == LEFT:
            return self.left
        elif direction == RIGHT:
            return self.right

    def __str__(self):
        return f"{'n/a' if self.card is None else self.card}({'R' if self.belongs_to == RED else 'B' if self.belongs_to == BLUE else '-'})"

    def __bool__(self):
        return self.card is not None


class HandCard(object):
    def __init__(self, hand_card_id: int):
        self.public = bool(hand_card_id & 0xf000)
        self.card_id = hand_card_id & 0xfff
        self.card = Card.get_card(self.card_id) if self.card_id else None

    def __hash__(self):
        return self.card_id

    def __str__(self):
        return "Unknown" if self.card is None else str(self.card)

    def copy(self):
        return deepcopy(self)



class Game(object):
    def __init__(self, first_player: int, blue_cards: list[int], red_cards: list[int], rules: list[int]):
        self.round = 0
        self.blocks = [Block(self, i) for i in range(9)]
        self.current_player = first_player
        self.blue_cards: list[Optional[HandCard]] = [HandCard(card_id) for card_id in blue_cards]
        self.red_cards: list[Optional[HandCard]] = [HandCard(card_id) for card_id in red_cards]
        self.rules = set(rules)
        if 0 in self.rules:
            self.rules.remove(0)
        self.type_cnt = dict()

    def __str__(self):
        return f"""==={self.round}({'R' if self.current_player == RED else 'B' if self.current_player == BLUE else '-'})===
rules: {','.join([rule_sheet[rule]['Name'] for rule in self.rules])}
blue card: {','.join(map(str, self.blue_cards))}
red card: {','.join(map(str, self.red_cards))}
types: {' , '.join([f"{k}:{v}" for k, v in self.type_cnt.items()])}
{' | '.join(map(str, self.blocks[:3]))}
{' | '.join(map(str, self.blocks[3:6]))}
{' | '.join(map(str, self.blocks[6:9]))}
"""

    def win(self):
        if sum(map(bool, self.blocks)) < 9:
            return
        result = sum(map(lambda x: x is not None, self.blue_cards)) - sum(map(lambda x: x is not None, self.red_cards))
        for block in self.blocks: result += block.belongs_to
        if result > 0:
            return BLUE
        elif result < 0:
            return RED
        else:
            return NONE

    def copy(self):
        return deepcopy(self)

    def get_type_cnt(self, card_type):
        if not card_type: return 0
        return self.type_cnt.setdefault(card_type, 0)

    def get_strength(self, card: Card, direction: int):
        base = card.get(direction)
        if 12 in self.rules: base = min(base + self.get_type_cnt(card.card_type), 10)  # 同类强化
        if 13 in self.rules: base = max(base - self.get_type_cnt(card.card_type), 1)  # 同类弱化
        return base

    def card_win(self, card1: Card, card2: Card, direction: int):
        card1_base = self.get_strength(card1, direction)
        card2_base = self.get_strength(card2, -direction)

        reverse = 10 in self.rules  # 逆转

        if 11 in self.rules:  # 王牌杀手
            if card1_base == 10 and card2_base == 1:
                return reverse
            elif card1_base == 1 and card2_base == 10:
                return not reverse
        if reverse:
            return card1_base < card2_base
        else:
            return card1_base > card2_base

    def get_current_cards(self):
        return self.blue_cards if self.current_player == BLUE else self.red_cards

    def place_card(self, block_id: int, hand_id: int, card_id: int):
        if card_id > MAX_CARD_ID or card_id < 1:
            raise Exception(f"Invalid card_id: {card_id}")
        if hand_id > 4 or hand_id < 0:
            raise Exception(f"Invalid hand_id: {hand_id}")
        if block_id > 8 or block_id < 0:
            raise Exception(f"Invalid block_id: {block_id}")
        if self.blocks[block_id].card is not None:
            raise Exception(f"Block-{block_id} is occupied by a card already")

        self.round += 1

        card = Card.get_card(card_id)
        block = self.blocks[block_id]
        self.blocks[block_id].card = card
        self.blocks[block_id].belongs_to = self.current_player
        to_cal = {(card, block)}

        if 4 in self.rules:  # 同数
            pre_add = list()
            for direction in directions:
                target_block = block.get(direction)
                if target_block and target_block.card.get(-direction) == card.get(direction):
                    pre_add.append((target_block.card, target_block))
            if len(pre_add) > 1:
                for target_card, target_block in pre_add:
                    if target_block.belongs_to != self.current_player:
                        target_block.belongs_to = self.current_player
                        to_cal.add((target_card, target_block))

        if 6 in self.rules:  # 加算
            pre_adds = dict()
            for direction in directions:
                target_block = block.get(direction)
                if target_block:
                    strength_sum = target_block.card.get(-direction) + card.get(direction)
                    pre_adds.setdefault(strength_sum, list()).append((target_block.card, target_block))
            for pre_add in pre_adds.values():
                if len(pre_add) > 1:
                    for target_card, target_block in pre_add:
                        if target_block.belongs_to != self.current_player:
                            target_block.belongs_to = self.current_player
                            to_cal.add((target_card, target_block))

        while to_cal:
            cal_card, cal_block = to_cal.pop()
            for direction in directions:
                target_block = cal_block.get(direction)
                if target_block and self.card_win(cal_card, target_block.card, direction):
                    target_block.belongs_to = self.current_player

        if card.card_type:
            self.type_cnt[card.card_type] = self.get_type_cnt(card.card_type) + 1
        self.get_current_cards()[hand_id] = None
        self.current_player = -self.current_player

        return self
