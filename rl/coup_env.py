import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from enum import Enum

class Card(Enum):
    DUKE = 0
    ASSASSIN = 1
    AMBASSADOR = 2
    CAPTAIN = 3
    CONTESSA = 4

class Action(Enum):
    INCOME = 0
    FOREIGN_AID = 1
    COUP = 2
    TAX = 3
    ASSASSINATE = 4
    EXCHANGE = 5
    STEAL = 6

NUM_PLAYERS = 3  # Will increase to more later

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.coins = 2
        self.cards = []
        self.alive = True

    def lose_influence(self):
        if self.cards:
            self.cards.pop()
        if not self.cards:
            self.alive = False

    def is_active(self):
        return self.alive

    def get_legal_actions(self):
        if self.coins >= 10:
            return [Action.COUP]
        actions = list(Action)
        if self.coins < 3:
            actions = [a for a in actions if a != Action.ASSASSINATE]
        if self.coins < 7:
            actions = [a for a in actions if a != Action.COUP]
        return actions


class CoupEnv(gym.Env):
    def __init__(self):
        super(CoupEnv, self).__init__()
        self.players = [Player(i) for i in range(NUM_PLAYERS)]
        self.current_player = 0
        self.deck = []
        self.winner = None

        self.observation_space = spaces.Box(low=0, high=10, shape=(NUM_PLAYERS * 2,), dtype=np.int32)
        self.action_space = spaces.Discrete(len(Action))

    def reset(self, seed=None, options=None):
        self.deck = [card for card in Card] * 3
        random.shuffle(self.deck)
        for p in self.players:
            p.coins = 2
            p.alive = True
            p.cards = [self.deck.pop(), self.deck.pop()]
        self.current_player = 0
        return self._get_obs(), {}

    def _get_obs(self):
        obs = []
        for p in self.players:
            obs.append(p.coins)
            obs.append(len(p.cards))
        return np.array(obs, dtype=np.int32)

    def step(self, action_idx):
        action = Action(action_idx)
        player = self.players[self.current_player]

        if not player.alive:
            self._next_player()
            return self._get_obs(), 0, False, False, {}

        target = self._select_target()
        reward = 0
        terminated = False

        # Get legal actions
        legal_actions = player.get_legal_actions()

        # Special Coup override rule at 10+ coins
        if player.coins >= 10 and action != Action.COUP:
            # Enforce mandatory Coup
            reward = -10  # big penalty for illegal skip of coup
            terminated = False
            self._next_player()
            return self._get_obs(), reward, terminated, False, {
                "reason": "Coup required with 10+ coins"
            }

        # ILLEGAL ACTION handling
        if action not in legal_actions:
            # Option A (preferred): block and penalize
            reward = -5
            terminated = False
            self._next_player()
            return self._get_obs(), reward, terminated, False, {
                "reason": f"Illegal action: {action.name}"
            }

        # LEGAL ACTIONS
        if action == Action.INCOME:
            player.coins += 1
        elif action == Action.FOREIGN_AID:
            player.coins += 2
        elif action == Action.TAX:
            player.coins += 3
        elif action == Action.COUP and target:
            player.coins -= 7
            target.lose_influence()
        elif action == Action.ASSASSINATE and target:
            player.coins -= 3
            target.lose_influence()
        elif action == Action.STEAL and target:
            stolen = min(2, target.coins)
            target.coins -= stolen
            player.coins += stolen
        elif action == Action.EXCHANGE:
            drawn = [self.deck.pop() for _ in range(2)]
            self.deck.extend(drawn)
            random.shuffle(self.deck)

        # Check win condition
        if self._check_win(player):
            reward = 1
            terminated = True

        self._next_player()
        return self._get_obs(), reward, terminated, False, {}


    def _check_win(self, player):
        alive_players = [p for p in self.players if p.alive]
        return len(alive_players) == 1 and player.alive

    def _select_target(self):
        candidates = [p for p in self.players if p.id != self.current_player and p.alive]
        return random.choice(candidates) if candidates else None

    def _next_player(self):
        while True:
            self.current_player = (self.current_player + 1) % NUM_PLAYERS
            if self.players[self.current_player].alive:
                break

    def render(self):
        for p in self.players:
            print(f"Player {p.id}: {p.coins} coins, {len(p.cards)} cards, {'alive' if p.alive else 'dead'}")
        print(f"Current player: {self.current_player}\n")
