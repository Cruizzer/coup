import random
from bots.random_bot import RandomBot
from env.coup_env import CoupEnv
from game.actions import Action
from game.cards import Card
from game.game_state import GameState

def simulate_random_game(num_players=3):
    game = GameState(num_players)

    while not game.is_game_over():
        player = game.get_current_player()
        player_id = player.id
        legal_actions = game.get_legal_actions(player_id)
        action = random.choice(legal_actions)

        target_id = None
        if action in [Action.ASSASSINATE, Action.STEAL, Action.COUP]:
            targets = [p.id for p in game.players if p.id != player_id and p.is_alive()]
            if targets:
                target_id = random.choice(targets)

        claim_card = None
        if action == Action.TAX:
            claim_card = Card.DUKE
        elif action == Action.ASSASSINATE:
            claim_card = Card.ASSASSIN
        elif action == Action.STEAL:
            claim_card = Card.CAPTAIN
        elif action == Action.EXCHANGE:
            claim_card = Card.AMBASSADOR

        game.perform_action(player_id, action, target_id, claim_card)

    print(f"Game over! Winner: Player {game.get_winner()}")



if __name__ == "__main__":
    simulate_random_game()
