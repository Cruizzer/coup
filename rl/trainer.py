import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure
from coup_env import CoupEnv

def train_agent():
    env = make_vec_env(lambda: Monitor(CoupEnv()), n_envs=1)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=1024,
        batch_size=64,
        gae_lambda=0.95,
        gamma=0.99,
        n_epochs=10,
        ent_coef=0.01,
        device="cpu"
    )

    model.learn(total_timesteps=100_000)
    model.save("ppo_coup")

if __name__ == "__main__":
    train_agent()
