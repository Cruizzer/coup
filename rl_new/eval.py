import numpy as np
from stable_baselines3 import PPO
from coup_env import env as coup_env_factory, Action

NUM_PLAYERS = 4
MODEL_PATHS = [f"ppo_agent_{i}" for i in range(NUM_PLAYERS)]

def main():
    env = coup_env_factory()
    env.reset()

    models = [PPO.load(path) for path in MODEL_PATHS]

    round_num = 0
    print("\n===== Starting Evaluation Game =====\n")

    while True:
        current_agent = env.agent_selection
        agent_idx = int(current_agent.split("_")[1])
        player = env.players[agent_idx]

        if env.dones[current_agent]:
            env.step(None)
            continue

        obs = env.observe(current_agent)

        print(f"\n--- Round {round_num}, Agent: {current_agent} ---")
        print(f"Coins: {player.coins}, Cards: {[c.name for c in player.cards]}, Alive: {player.alive}")

        # Predict action
        action, _ = models[agent_idx].predict(obs, deterministic=True)
        action_enum = Action(action)

        print(f"Chosen Action: {action_enum.name} ({action})")

        # Save state before step
        before_coins = player.coins
        before_cards = len(player.cards)

        # Step
        env.step(action)

        # Show result of action
        after_coins = player.coins
        after_cards = len(player.cards)
        coin_change = after_coins - before_coins
        card_change = after_cards - before_cards

        print(f"After Action: Coins = {after_coins} (Δ{coin_change}), Cards = {after_cards} (Δ{card_change})")
        print(f"Alive: {player.alive}")

        # Render current state
        print("\n[Game State]")
        env.render()

        round_num += 1

        # End condition
        if all(env.dones.values()):
            print("\n===== GAME OVER =====")
            for i, p in enumerate(env.players):
                print(f"Player {i}: Alive={p.alive}, Coins={p.coins}, Cards={len(p.cards)}")
            break

if __name__ == "__main__":
    main()
