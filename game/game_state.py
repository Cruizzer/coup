import random
from collections import deque
from game.actions import Action
from game.cards import Card
from game.player import Player


class GameState:
    def __init__(self, num_players):
        self.num_players = num_players
        self.players = [Player(i) for i in range(num_players)]
        self.deck = self._init_deck()
        self.current_player_idx = 0
        self.action_stack = deque()
        self.history = []
        self._deal_initial_cards()

    def _init_deck(self):
        deck = Card.ALL_CARDS * 3
        random.shuffle(deck)
        return deck

    def _deal_initial_cards(self):
        for player in self.players:
            player.cards = [self.deck.pop(), self.deck.pop()]

    def get_current_player(self):
        return self.players[self.current_player_idx]

    def get_alive_players(self):
        return [p for p in self.players if p.is_alive()]

    def next_player(self):
        start_idx = self.current_player_idx
        while True:
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players
            if self.players[self.current_player_idx].is_alive():
                break
            if self.current_player_idx == start_idx:
                break

    def is_game_over(self):
        return len(self.get_alive_players()) == 1

    def get_winner(self):
        if self.is_game_over():
            return self.get_alive_players()[0].id
        return None

    def challenge(self, challenger_id, target_id, claimed_card):
        target = self.players[target_id]
        challenger = self.players[challenger_id]
        if claimed_card in target.cards:
            # Challenge fails
            challenger.lose_influence()
            # Target returns and redraws card
            target.cards.remove(claimed_card)
            self.deck.append(claimed_card)
            random.shuffle(self.deck)
            target.cards.append(self.deck.pop())
            return True  # action proceeds
        else:
            # Challenge succeeds
            target.lose_influence()
            return False  # action fails

    def perform_action(self, player_id, action, target_id=None, claim_card=None, block_by=None, challenged_by=None):
        player = self.players[player_id]
        if not player.is_alive():
            return False

        action_valid = True
        block_success = False

        # Handle challenges
        if challenged_by is not None:
            action_valid = self.challenge(challenged_by, player_id, claim_card)
            if not action_valid:
                self.history.append((challenged_by, Action.CHALLENGE, player_id, claim_card))
                self.next_player()
                return False

        # Handle blocks
        if block_by is not None:
            if action == Action.FOREIGN_AID:
                block_success = True
            elif action == Action.ASSASSINATE and claim_card == Card.ASSASSIN:
                block_success = self.challenge(player_id, block_by, Card.CONTESSA) if challenged_by is not None else True
            elif action == Action.STEAL:
                block_success = self.challenge(player_id, block_by, Card.CAPTAIN) if challenged_by is not None else True
            if block_success:
                self.history.append((block_by, 'block', action))
                self.next_player()
                return False

        # Resolve actions
        if action == Action.INCOME:
            player.coins += 1
        elif action == Action.FOREIGN_AID:
            player.coins += 2
        elif action == Action.COUP and target_id is not None and player.coins >= 7:
            player.coins -= 7
            self.players[target_id].lose_influence()
        elif action == Action.TAX:
            player.coins += 3
        elif action == Action.ASSASSINATE and target_id is not None and player.coins >= 3:
            player.coins -= 3
            self.players[target_id].lose_influence()
        elif action == Action.STEAL and target_id is not None:
            target = self.players[target_id]
            stolen = min(2, target.coins)
            target.coins -= stolen
            player.coins += stolen
        elif action == Action.EXCHANGE:
            drawn = [self.deck.pop(), self.deck.pop()]
            kept = player.cards + drawn
            random.shuffle(kept)
            player.cards = kept[:2]
            self.deck += kept[2:]
            random.shuffle(self.deck)

        self.history.append((player_id, action, target_id, claim_card))
        self.next_player()
        return True

    def get_legal_actions(self, player_id):
        player = self.players[player_id]
        if not player.is_alive():
            return []

        actions = [Action.INCOME, Action.FOREIGN_AID, Action.TAX, Action.EXCHANGE]
        if player.coins >= 7:
            actions.append(Action.COUP)
        if player.coins >= 3:
            actions.append(Action.ASSASSINATE)
        actions.append(Action.STEAL)
        return actions