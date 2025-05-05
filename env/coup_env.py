from game.game_state import GameState

class CoupEnv:
    def __init__(self, num_players):
        self.game = GameState(num_players)

    def reset(self):
        self.game = GameState(len(self.game.players))
        self.game.deal_initial_cards()
        return self._get_observation()

    def step(self, action):
        # Pass action to game, resolve it, return new observation
        pass

    def _get_observation(self):
        # Return partial observation for current player
        pass

    def render(self):
        # Optional text-based or GUI visualization
        pass
