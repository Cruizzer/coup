from stable_baselines3 import PPO
from coup_env import CoupEnv

env = CoupEnv()
model = PPO.load("ppo_coup_multiagent")

obs, _ = env.reset()
done = False
total_reward = 0

while not done:
    env.render()
    action, _ = model.predict(obs)
    obs, reward, terminated, truncated, _ = env.step(action)
    done = terminated or truncated
    total_reward += reward

env.render()
print(f"Total reward: {total_reward}")
