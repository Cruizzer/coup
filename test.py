# Full base game engine for Coup with bluffing and blocking
import random
from collections import deque

class Card:
    DUKE = "Duke"
    ASSASSIN = "Assassin"
    CAPTAIN = "Captain"
    AMBASSADOR = "Ambassador"
    CONTESSA = "Contessa"
    ALL_CARDS = [DUKE, ASSASSIN, CAPTAIN, AMBASSADOR, CONTESSA]

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.coins = 2
        self.cards = []
        self.lost_cards = []
        self.alive = True

    def is_alive(self):
        return len(self.cards) > 0

    def lose_influence(self, card_to_lose=None):
        if card_to_lose and card_to_lose in self.cards:
            self.cards.remove(card_to_lose)
        elif self.cards:
            self.cards.pop()
        if not self.cards:
            self.alive = False
        print(f"Player {self.id} loses a card. Remaining hand: {self.cards}")


class Action:
    INCOME = "income"
    FOREIGN_AID = "foreign_aid"
    COUP = "coup"
    TAX = "tax"
    ASSASSINATE = "assassinate"
    STEAL = "steal"
    EXCHANGE = "exchange"
    BLOCK_FOREIGN_AID = "block_foreign_aid"
    BLOCK_STEAL = "block_steal"
    BLOCK_ASSASSINATE = "block_assassinate"
    CHALLENGE = "challenge"

    PRIMARY_ACTIONS = [INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE]
    BLOCK_ACTIONS = [BLOCK_FOREIGN_AID, BLOCK_STEAL, BLOCK_ASSASSINATE]

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
        print(f"Player {challenger_id} challenges Player {target_id}'s claim of {claimed_card}.")
        if claimed_card in target.cards:
            print(f"Challenge failed! Player {target_id} had {claimed_card}.")
            challenger.lose_influence()
            try:
                target.cards.remove(claimed_card)
            except ValueError:
                print(f"WARNING: {claimed_card} not in Player {target_id}'s hand during challenge resolution.")
                return True
            self.deck.append(claimed_card)
            random.shuffle(self.deck)
            target.cards.append(self.deck.pop())
            return True
        else:
            print(f"Challenge successful! Player {target_id} did not have {claimed_card}.")
            target.lose_influence()
            return False

    def block_action(self, blocker_id, action, challenger_id=None):
        required_card = None
        if action == Action.FOREIGN_AID:
            required_card = Card.DUKE
        elif action == Action.ASSASSINATE:
            required_card = Card.CONTESSA
        elif action == Action.STEAL:
            required_card = Card.CAPTAIN

        if challenger_id is not None:
            return self.challenge(challenger_id, blocker_id, required_card)

        print(f"Player {blocker_id} blocks action {action} using {required_card}.")
        return True

    def perform_action(self, player_id, action, target_id=None, claim_card=None, block_by=None, challenged_by=None):
        player = self.players[player_id]
        if not player.is_alive():
            return False

        if action in Action.PRIMARY_ACTIONS:
            print(f"Player {player_id} attempts to perform {action}" + 
                (f" on Player {target_id}" if target_id is not None else "") + 
                (f" claiming {claim_card}" if claim_card else "") + 
                f" | Coins: {player.coins}")

        action_valid = True
        if challenged_by is not None and claim_card:
            action_valid = self.challenge(challenged_by, player_id, claim_card)
            if not action_valid:
                self.history.append((challenged_by, Action.CHALLENGE, player_id, claim_card))
                self.next_player()
                return False

        if block_by is not None:
            # Ensure only valid targets can block actions affecting them
            if action in [Action.STEAL, Action.ASSASSINATE] and block_by != target_id:
                block_by = None
            if action == Action.FOREIGN_AID and block_by == player_id:
                block_by = None

        if block_by is not None:
            block_valid = self.block_action(block_by, action, challenged_by)
            if block_valid:
                print(f"Action {action} by Player {player_id} was blocked by Player {block_by}.")
                self.next_player()
                return False

        print(f"Player {player_id} performs {action}" + (f" on Player {target_id}" if target_id is not None else "") + (f" claiming {claim_card}" if claim_card else ""))

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
            num_to_draw = 2 if len(player.cards) == 2 else 1
            drawn = [self.deck.pop() for _ in range(num_to_draw)]
            print(f"Player {player_id} draws {drawn} using Ambassador.")

            combined = player.cards + drawn
            random.shuffle(combined)
            player.cards = combined[:2]

            returned = combined[2:]
            self.deck += returned
            random.shuffle(self.deck)

            # Output the player's hand after the exchange
            print(f"Player {player_id}'s new hand after exchange: {player.cards}")




        self.history.append((player_id, action, target_id, claim_card))
        self.next_player()

        print("----")

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

        # Only allow STEAL if there's a valid target with at least 1 coin
        steal_targets = [
            p for p in self.players
            if p.id != player_id and p.is_alive() and p.coins >= 2
        ]
        if steal_targets:
            actions.append(Action.STEAL)

        return actions
    

def simulate_random_game(num_players=3):
    game = GameState(num_players)
    print("Starting a new game of Coup")
    for p in game.players:
        print(f"Player {p.id} starts with: {p.cards}")

    while not game.is_game_over():
        player = game.get_current_player()
        player_id = player.id
        legal_actions = game.get_legal_actions(player_id)
        action = random.choice(legal_actions)

        target_id = None
        if action in [Action.ASSASSINATE, Action.STEAL, Action.COUP]:
            if action == Action.STEAL:
                targets = [p.id for p in game.players if p.id != player_id and p.is_alive() and p.coins >= 2]
            else:
                targets = [p.id for p in game.players if p.id != player_id and p.is_alive()]
            if targets:
                target_id = random.choice(targets)
            else:
                # Skip this action if no valid targets
                continue


        claim_card = None
        if action == Action.TAX:
            claim_card = Card.DUKE
        elif action == Action.ASSASSINATE:
            claim_card = Card.ASSASSIN
        elif action == Action.STEAL:
            claim_card = Card.CAPTAIN
        elif action == Action.EXCHANGE:
            claim_card = Card.AMBASSADOR

        block_by = None
        challenged_by = None

        if action == Action.FOREIGN_AID and random.random() < 0.3:
            block_candidates = [p.id for p in game.players if p.id != player_id and p.is_alive()]
            if block_candidates:
                block_by = random.choice(block_candidates)
                challengers = [p.id for p in game.players if p.id != block_by and p.is_alive()]
                if challengers and random.random() < 0.5:
                    challenged_by = random.choice(challengers)

        elif action == Action.ASSASSINATE and target_id is not None and random.random() < 0.3:
            block_by = target_id
            challengers = [p.id for p in game.players if p.id != block_by and p.is_alive()]
            if challengers and random.random() < 0.5:
                challenged_by = random.choice(challengers)

        elif action == Action.STEAL and target_id is not None and random.random() < 0.3:
            block_by = target_id
            challengers = [p.id for p in game.players if p.id != block_by and p.is_alive()]
            if challengers and random.random() < 0.5:
                challenged_by = random.choice(challengers)

        elif claim_card and random.random() < 0.3:
            challengers = [p.id for p in game.players if p.is_alive()]
            if challengers:
                challenged_by = random.choice(challengers)

        game.perform_action(player_id, action, target_id, claim_card, block_by, challenged_by)

    print(f"Game over! Winner: Player {game.get_winner()}")

simulate_random_game()