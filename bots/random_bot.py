import random

class RandomBot:
    def choose_action(self, observation, legal_actions):
        return random.choice(legal_actions)
