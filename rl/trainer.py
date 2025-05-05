class Trainer:
    def __init__(self, env, agent):
        self.env = env
        self.agent = agent

    def train(self, episodes):
        for ep in range(episodes):
            state = self.env.reset()
            done = False
            while not done:
                action = self.agent.select_action(state)
                state, reward, done, info = self.env.step(action)
            # Use REINFORCE to update policy after episode
