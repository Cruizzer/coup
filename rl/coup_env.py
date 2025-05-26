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

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.coins = 2
        self.cards = []
        self.alive = True

    def lose_influence(self):
        if not self.cards:
            return
        lost_card = self.cards.pop(random.randint(0, len(self.cards)-1))
        if not self.cards:
            self.alive = False

    def get_legal_actions(self):
        actions = list(Action)
        if self.coins < 3:
            actions = [a for a in actions if a != Action.ASSASSINATE]
        if self.coins < 7:
            actions = [a for a in actions if a != Action.COUP]
        return actions

class CoupEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 4}

    def __init__(self):
        super().__init__()
        self.num_players = 2
        self.deck = []
        self.players = [Player(i) for i in range(self.num_players)]
        self.current_player_idx = 0

        # Obs space: each player’s coins (2), cards (2), alive flag (1)
        self.observation_space = spaces.Box(low=0, high=10, shape=(self.num_players * 5,), dtype=np.float32)
        self.action_space = spaces.Discrete(len(Action))

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.deck = [card for card in Card] * 3
        random.shuffle(self.deck)
        self.players = [Player(i) for i in range(self.num_players)]
        for player in self.players:
            player.cards = [self.deck.pop(), self.deck.pop()]
            player.coins = 2
            player.alive = True
        self.current_player_idx = 0
        return self._get_obs(), {}

    def _get_obs(self):
        obs = []
        for p in self.players:
            obs.extend([
                p.coins,
                p.cards[0].value if len(p.cards) > 0 else -1,
                p.cards[1].value if len(p.cards) > 1 else -1,
                int(p.alive),
                len(p.cards)
            ])
        return np.array(obs, dtype=np.float32)

    def step(self, action):
        player = self.players[self.current_player_idx]
        opponent = self.players[1 - self.current_player_idx]

        reward = 0
        terminated = False
        truncated = False

        # Action logic
        if not player.alive:
            self.current_player_idx = 1 - self.current_player_idx
            return self._get_obs(), reward, terminated, truncated, {}

        if action == Action.INCOME.value:
            player.coins += 1
        elif action == Action.FOREIGN_AID.value:
            player.coins += 2
        elif action == Action.COUP.value and player.coins >= 7:
            player.coins -= 7
            opponent.lose_influence()
        elif action == Action.TAX.value:
            player.coins += 3
        elif action == Action.ASSASSINATE.value and player.coins >= 3:
            player.coins -= 3
            opponent.lose_influence()
        elif action == Action.STEAL.value:
            stolen = min(2, opponent.coins)
            opponent.coins -= stolen
            player.coins += stolen
        elif action == Action.EXCHANGE.value:
            drawn = [self.deck.pop(), self.deck.pop()]
            self.deck.extend(player.cards)
            random.shuffle(self.deck)
            player.cards = drawn[:2]

        # Check if opponent died
        if not opponent.alive:
            reward = 1  # win reward
            terminated = True

        self.current_player_idx = 1 - self.current_player_idx
        return self._get_obs(), reward, terminated, truncated, {}

    def render(self):
        for p in self.players:
            print(f"Player {p.id} | Coins: {p.coins} | Cards: {len(p.cards)} | Alive: {p.alive}")
