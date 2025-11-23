from coup_env import CoupEnv

env = CoupEnv()
obs = env.reset()

while not all(env.dones.values()):
    print("\nCurrent Phase:", env.phase)
    print("Pending Action:", env.pending_action if hasattr(env, 'pending_action') else "None")
    print("Agent to act:", env.agent_selection)
    env.render()

    current_agent = env.agent_selection
    legal = env._legal_actions(current_agent)
    print(f"Agent: {current_agent}, Legal actions: {legal}")

    # If phase is challenge or counteraction, we need to ask other players in order:
    if env.phase in ['challenge', 'counteraction']:
        # loop over all other agents for challenge or block responses
        for agent in env.agents:
            if agent == current_agent or env.dones[agent]:
                continue
            print(f"Agent {agent}, respond to {env.phase} (challenge/block/pass)")
            resp_legal = env._legal_actions(agent)
            print(f"Legal actions for response: {resp_legal}")
            while True:
                try:
                    response = int(input(f"Enter action number for {agent}: "))
                    if response in resp_legal:
                        break
                    else:
                        print("Invalid action for response, try again.")
                except ValueError:
                    print("Invalid input, enter a number.")
            # You will need to advance env.agent_selection manually here or call env.step
            env.agent_selection = agent
            env.step(response)
            env.render()

        # After all responses, continue main agent action or resolve
        env.agent_selection = current_agent
        continue

    # Normal turn action input
    while True:
        try:
            action = int(input("Enter action number: "))
            if action in legal:
                break
            else:
                print("Invalid action, try again.")
        except ValueError:
            print("Invalid input, enter a number.")

    env.step(action)
