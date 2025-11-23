import gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecEnv
from stable_baselines3.common.env_util import make_vec_env
from coup_env import env as coup_env_factory
import os

NUM_PLAYERS = 4
TIMESTEPS = 100000  # Adjust as needed

def make_agent_env(player_id):
    env = coup_env_factory()
    env.reset()
    # Wrap to provide only this player's observations and actions
    class SingleAgentWrapper(gym.Env):
        def __init__(self, env, player_id):
            super().__init__()
            self.env = env
            self.player_id = player_id
            self.agent = f"player_{player_id}"
            self.action_space = env.action_spaces[self.agent]
            self.observation_space = gym.spaces.Box(low=0, high=1, shape=(len(env.observe(self.agent)),), dtype=np.float32)

        def reset(self):
            self.env.reset()
            obs = self.env.observe(self.agent)
            return obs

        def step(self, action):
            done = False
            reward = 0
            info = {}
            # PettingZoo requires advancing through all agents, so we step env until our turn again
            while True:
                current_agent = self.env.agent_selection
                if current_agent == self.agent:
                    self.env.step(action)
                else:
                    self.env.step(self.env.action_spaces[current_agent].sample())

                if self.env.dones[self.agent]:
                    done = True
                    reward = self.env.rewards[self.agent]
                    obs = np.zeros_like(self.env.observe(self.agent))
                    break

                if self.env.agent_selection == self.agent:
                    obs = self.env.observe(self.agent)
                    reward = self.env.rewards[self.agent]
                    break

            return obs, reward, done, info

        def render(self, mode='human'):
            self.env.render(mode)

    return SingleAgentWrapper(env, player_id)

def main():
    agents = []
    for i in range(NUM_PLAYERS):
        env = make_agent_env(i)
        vec_env = DummyVecEnv([lambda: env])
        model = PPO("MlpPolicy", vec_env, verbose=1)
        agents.append((model, env))

    # Training loop for all agents (independent learning)
    for i, (model, env) in enumerate(agents):
        print(f"Training agent {i}...")
        model.learn(total_timesteps=TIMESTEPS)
        model.save(f"ppo_agent_{i}")

if __name__ == "__main__":
    main()
