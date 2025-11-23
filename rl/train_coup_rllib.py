# train_coup_rllib.py

import os
# Set env vars BEFORE importing ray to avoid Windows handle errors
os.environ["RAY_LOG_TO_STDERR"] = "1"          # Log to stderr, no redirection
os.environ["RAY_BACKEND_LOG_LEVEL"] = "ERROR"  # Optional: reduce logging verbosity

import ray
from ray import tune
from ray.rllib.env.multi_agent_env import MultiAgentEnv
from gymnasium import spaces
import numpy as np
import random
from enum import Enum

# ----------- Coup environment classes -----------------

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

NUM_PLAYERS = 3

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

    def get_legal_actions(self):
        actions = list(Action)
        if self.coins < 3:
            actions = [a for a in actions if a != Action.ASSASSINATE]
        if self.coins < 7:
            actions = [a for a in actions if a != Action.COUP]
        # Must coup if 10 or more coins
        if self.coins >= 10:
            return [Action.COUP]
        return actions

class CoupMultiAgentEnv(MultiAgentEnv):
    def __init__(self):
        self.players = [Player(i) for i in range(NUM_PLAYERS)]
        self.deck = [card for card in Card] * 3
        random.shuffle(self.deck)
        for p in self.players:
            p.cards = [self.deck.pop(), self.deck.pop()]
        self.current_player = 0
        self.done = False

        # Observation space: for each player, coins and cards count
        self.observation_space = spaces.Box(low=0, high=10, shape=(NUM_PLAYERS * 2,), dtype=np.int32)
        self.action_space = spaces.Discrete(len(Action))

    def reset(self):
        self.deck = [card for card in Card] * 3
        random.shuffle(self.deck)
        for p in self.players:
            p.coins = 2
            p.alive = True
            p.cards = [self.deck.pop(), self.deck.pop()]
        self.current_player = 0
        self.done = False
        return self._get_obs()

    def _get_obs(self):
        obs = []
        for p in self.players:
            obs.append(p.coins)
            obs.append(len(p.cards))
        return {str(p.id): np.array(obs, dtype=np.int32) for p in self.players if p.alive}

    def step(self, action_dict):
        if self.done:
            return {}, {}, {}, {}

        rewards = {str(p.id): 0 for p in self.players if p.alive}
        dones = {}
        infos = {}

        current_id = str(self.current_player)
        player = self.players[self.current_player]

        # Check legal action
        legal_actions = player.get_legal_actions()
        action = Action(action_dict[current_id])
        if action not in legal_actions:
            # Illegal action penalty and skip turn
            rewards[current_id] = -1
            dones = {str(p.id): False for p in self.players if p.alive}
            dones["__all__"] = False
            self._next_player()
            return self._get_obs(), rewards, dones, infos

        # Select a target if action requires it
        target = None
        if action in [Action.COUP, Action.ASSASSINATE, Action.STEAL]:
            targets = [p for p in self.players if p.id != player.id and p.alive]
            if targets:
                target = random.choice(targets)

        # Perform action effects
        if action == Action.INCOME:
            player.coins += 1
        elif action == Action.FOREIGN_AID:
            player.coins += 2
        elif action == Action.TAX:
            player.coins += 3
        elif action == Action.COUP:
            player.coins -= 7
            target.lose_influence()
        elif action == Action.ASSASSINATE:
            player.coins -= 3
            target.lose_influence()
        elif action == Action.STEAL:
            stolen = min(2, target.coins)
            target.coins -= stolen
            player.coins += stolen
        elif action == Action.EXCHANGE:
            # Simplified: draw 2 cards, pick 2 best (random here)
            drawn = [self.deck.pop() for _ in range(2)]
            combined = player.cards + drawn
            random.shuffle(combined)
            player.cards = combined[:2]
            self.deck.extend(combined[2:])
            random.shuffle(self.deck)

        # Check for win
        alive_players = [p for p in self.players if p.alive]
        if len(alive_players) == 1:
            rewards[str(alive_players[0].id)] = 1
            self.done = True

        dones = {str(p.id): not p.alive for p in self.players}
        dones["__all__"] = self.done

        self._next_player()

        return self._get_obs(), rewards, dones, infos

    def _next_player(self):
        for _ in range(NUM_PLAYERS):
            self.current_player = (self.current_player + 1) % NUM_PLAYERS
            if self.players[self.current_player].alive:
                return

    def render(self):
        for p in self.players:
            print(f"Player {p.id}: coins={p.coins}, cards={len(p.cards)}, alive={p.alive}")
        print(f"Current player: {self.current_player}")

# ----------------- Ray RLlib training setup ----------------

if __name__ == "__main__":
    ray.init(include_dashboard=False, ignore_reinit_error=True)

    from ray.rllib.algorithms.ppo import PPO

    def env_creator(config):
        return CoupMultiAgentEnv()

    tune.register_env("coup_multi", env_creator)

    policy_ids = [str(i) for i in range(NUM_PLAYERS)]

    def gen_policy():
        return (None,  # use default policy model
                CoupMultiAgentEnv().observation_space,
                CoupMultiAgentEnv().action_space,
                {})

    policies = {pid: gen_policy() for pid in policy_ids}

    # Policy mapping: each player controls own policy
    def policy_mapping_fn(agent_id):
        return agent_id

    config = {
        "env": "coup_multi",
        "num_workers": 0,  # run locally
        "multiagent": {
            "policies": policies,
            "policy_mapping_fn": policy_mapping_fn,
        },
        "framework": "torch",  # or "tf"
        "log_level": "WARN",
    }

    trainer = PPO(config=config)

    # Train loop
    for i in range(20):  # run 20 iterations
        result = trainer.train()
        print(f"Iteration {i}: reward_mean={result['episode_reward_mean']}")

    ray.shutdown()
