from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from coup_env import CoupEnv

def train_agent():
    env = CoupEnv()
    check_env(env, warn=True)

    model = PPO("MlpPolicy", env, verbose=1, n_steps=2048, batch_size=64)
    model.learn(total_timesteps=100_000)

    model.save("ppo_coup_multiagent")
    print("Model saved!")

if __name__ == "__main__":
    train_agent()
