from pettingzoo import AECEnv
from pettingzoo.utils import wrappers
from pettingzoo.utils.agent_selector import agent_selector
import numpy as np
import random
from enum import Enum
from gym.spaces import Discrete

class Card(Enum):
    DUKE = 0
    ASSASSIN = 1
    AMBASSADOR = 2
    CAPTAIN = 3
    CONTESSA = 4

class Action(Enum):
    INCOME = 0
    FOREIGN_AID = 1
    COUP = 2
    TAX = 3
    ASSASSINATE = 4
    EXCHANGE = 5
    STEAL = 6
    PASS = 7  # For challenge/counter phases to pass

# Helper functions for card requirements and counters
def required_card_for_action(action):
    mapping = {
        Action.TAX.value: Card.DUKE,
        Action.ASSASSINATE.value: Card.ASSASSIN,
        Action.STEAL.value: Card.CAPTAIN,
        Action.EXCHANGE.value: Card.AMBASSADOR,
    }
    return mapping.get(action, None)

def can_be_countered(action):
    return action in [Action.FOREIGN_AID.value, Action.STEAL.value, Action.ASSASSINATE.value]

def possible_counters(action):
    mapping = {
        Action.FOREIGN_AID.value: [Card.DUKE],
        Action.STEAL.value: [Card.CAPTAIN, Card.AMBASSADOR],
        Action.ASSASSINATE.value: [Card.CONTESSA],
    }
    return mapping.get(action, [])

class Player:
    def __init__(self, name):
        self.name = name
        self.coins = 2
        self.cards = []
        self.alive = True

    def lose_influence(self):
        if not self.cards:
            self.alive = False
            return None
        lost_card = self.cards.pop(random.randint(0, len(self.cards) - 1))
        if not self.cards:
            self.alive = False
        return lost_card

class CoupEnv(AECEnv):
    metadata = {'render_modes': ['human'], "name": "coup_v1"}

    def __init__(self, num_players=4):
        super().__init__()
        self.num_players = num_players
        self.agents = [f"player_{i}" for i in range(num_players)]
        self.possible_agents = self.agents[:]
        self.agent_name_mapping = {name: i for i, name in enumerate(self.agents)}

        self.action_spaces = {agent: Discrete(len(Action)) for agent in self.agents}
        self.observation_spaces = {agent: Discrete(2 ** (num_players * 10)) for agent in self.agents}  # dummy

        self.deck = []
        self.players = []
        self.agent_selection = None
        self._agent_selector = None
        self.rewards = {}
        self.dones = {}
        self.infos = {}

        self.history = []

        # New state variables for challenges and counteractions
        self.phase = "action_selection"
        self.pending_action = None
        self.pending_player = None
        self.pending_target = None
        self.claimed_card = None
        self.challenge_responders = []  # players who can challenge
        self.challenge_index = 0
        self.counteraction_player = None
        self.counteraction_card = None
        self.counter_challenge_responders = []
        self.counter_challenge_index = 0
        self.action_resolved = False

    def action_space(self, agent):
        return self.action_spaces[agent]

    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def _init_deck(self):
        self.deck = [card for card in Card] * 3
        random.shuffle(self.deck)

    def reset(self, seed=None, options=None):
        self._init_deck()
        self.players = [Player(agent) for agent in self.agents]
        for player in self.players:
            player.cards = [self.deck.pop(), self.deck.pop()]
            player.coins = 2
            player.alive = True

        self.agent_selection = self.agents[0]
        self._agent_selector = agent_selector(self.agents)
        self._agent_selector.reset()
        self.agent_selection = self._agent_selector.next()

        self.rewards = {agent: 0 for agent in self.agents}
        self.dones = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}

        self.history = []

        # Reset phases
        self.phase = "action_selection"
        self.pending_action = None
        self.pending_player = None
        self.pending_target = None
        self.claimed_card = None
        self.challenge_responders = []
        self.challenge_index = 0
        self.counteraction_player = None
        self.counteraction_card = None
        self.counter_challenge_responders = []
        self.counter_challenge_index = 0
        self.action_resolved = False

        return self._observe(self.agent_selection)

    def _observe(self, agent):
        idx = self.agent_name_mapping[agent]

        obs = []
        for i, p in enumerate(self.players):
            obs.append(p.coins / 10)
            obs.append(len(p.cards) / 2)
            obs.append(1.0 if p.alive else 0.0)
            if i == idx:
                card_vec = [0] * 5
                for c in p.cards:
                    card_vec[c.value] += 1
                obs.extend(card_vec)
            else:
                obs.extend([0] * 5)
        return np.array(obs, dtype=np.float32)

    def observe(self, agent):
        return self._observe(agent)

    def step(self, action):
        agent = self.agent_selection
        idx = self.agent_name_mapping[agent]
        player = self.players[idx]

        if self.dones[agent]:
            self._was_dead_step()
            return

        # Handle phases
        if self.phase == "action_selection":
            self._handle_action_selection(player, action)
        elif self.phase == "challenge":
            self._handle_challenge_phase(player, action)
        elif self.phase == "counter":
            self._handle_counter_phase(player, action)
        elif self.phase == "counter_challenge":
            self._handle_counter_challenge_phase(player, action)
        elif self.phase == "resolution":
            self._handle_resolution_phase()

        # Check end conditions
        alive_agents = [p.alive for p in self.players]
        if sum(alive_agents) == 1:
            winner_idx = alive_agents.index(True)
            for a in self.agents:
                self.rewards[a] = 0
                self.dones[a] = True
            self.rewards[self.agents[winner_idx]] = 1
            self._cumulative_rewards = self.rewards.copy()

        # If game not over, pick next agent if phase finished
        if self.phase == "action_selection":
            # Advance to next agent if no pending action
            self.agent_selection = self._agent_selector.next()

    def _handle_action_selection(self, player, action):
        agent = self.agent_selection
        legal_actions = self._legal_actions(agent)
        if action not in legal_actions:
            action = Action.INCOME.value  # Force legal action

        act_enum = Action(action)

        # Immediate actions without challenge/counter: INCOME, FOREIGN_AID (can be countered), COUP
        # Check if action requires claim and/or counter phase
        self.pending_action = action
        self.pending_player = player
        self.claimed_card = required_card_for_action(action)

        # Set possible targets for coup, assassinate, steal
        if action in [Action.COUP.value, Action.ASSASSINATE.value, Action.STEAL.value]:
            self.pending_target = self._choose_target(player)
        else:
            self.pending_target = None

        # If COUP (mandatory if coins >= 10), no challenge/counter
        if action == Action.COUP.value:
            player.coins -= 7
            if self.pending_target:
                self.pending_target.lose_influence()
            self.phase = "action_selection"
            self.agent_selection = self._agent_selector.next()
            return

        # For actions that require claim
        if self.claimed_card is not None:
            # Move to challenge phase for others to challenge claim
            self.phase = "challenge"
            # Other players except acting player can challenge
            self.challenge_responders = [a for a in self.agents if a != self.pending_player.name and self.players[self.agent_name_mapping[a]].alive]
            self.challenge_index = 0
            if not self.challenge_responders:
                # No one can challenge, skip challenge phase
                self.phase = "counter" if can_be_countered(action) else "resolution"
        else:
            # Actions without claim: INCOME or FOREIGN_AID (foreign aid can be countered)
            if action == Action.INCOME.value:
                player.coins += 1
                self.phase = "action_selection"
                self.agent_selection = self._agent_selector.next()
            elif action == Action.FOREIGN_AID.value:
                self.phase = "counter"
                self.challenge_responders = [a for a in self.agents if a != self.pending_player.name and self.players[self.agent_name_mapping[a]].alive]
                self.counteraction_player = None
                self.counteraction_card = None
                self.counter_challenge_responders = []
                self.counter_challenge_index = 0
                if not self.challenge_responders:
                    # No one to counter, apply action
                    self.pending_player.coins += 2
                    self.phase = "action_selection"
                    self.agent_selection = self._agent_selector.next()
            else:
                # Just in case
                self.phase = "action_selection"
                self.agent_selection = self._agent_selector.next()

    def _handle_challenge_phase(self, player, action):
        # This phase goes in order of challenge_responders
        # action==PASS (7) means no challenge
        responder = self.challenge_responders[self.challenge_index]
        if player.name != responder:
            # Wait for correct player to act
            return

        if action == Action.PASS.value:
            # No challenge, next challenger or move on
            self.challenge_index += 1
            if self.challenge_index >= len(self.challenge_responders):
                # No challenges, move to counter phase or resolution
                if can_be_countered(self.pending_action):
                    self.phase = "counter"
                    self.counteraction_player = None
                    self.counteraction_card = None
                    self.counter_challenge_responders = [a for a in self.agents if a != self.pending_player.name and self.players[self.agent_name_mapping[a]].alive]
                    self.counter_challenge_index = 0
                    if not self.counter_challenge_responders:
                        # No one to counter, apply action
                        self._apply_action()
                        self.phase = "action_selection"
                        self.agent_selection = self._agent_selector.next()
                else:
                    self._apply_action()
                    self.phase = "action_selection"
                    self.agent_selection = self._agent_selector.next()
            else:
                # Next challenger
                self.agent_selection = self.challenge_responders[self.challenge_index]
        else:
            # Challenge issued
            challenger = player
            claimant = self.pending_player

            # Check if claimant has the card
            if self.claimed_card in claimant.cards:
                # Claimant proves claim → challenger loses influence
                lost_card = challenger.lose_influence()
                # Claimant exchanges revealed card with deck
                claimant.cards.remove(self.claimed_card)
                self.deck.append(self.claimed_card)
                random.shuffle(self.deck)
                claimant.cards.append(self.deck.pop())

                # Challenge phase ends, move to counter phase or resolution
                if can_be_countered(self.pending_action):
                    self.phase = "counter"
                    self.counteraction_player = None
                    self.counteraction_card = None
                    self.counter_challenge_responders = [a for a in self.agents if a != self.pending_player.name and self.players[self.agent_name_mapping[a]].alive]
                    self.counter_challenge_index = 0
                    if not self.counter_challenge_responders:
                        self._apply_action()
                        self.phase = "action_selection"
                        self.agent_selection = self._agent_selector.next()
                else:
                    self._apply_action()
                    self.phase = "action_selection"
                    self.agent_selection = self._agent_selector.next()
            else:
                # Claimant lied → claimant loses influence, action fails
                lost_card = claimant.lose_influence()
                self.phase = "action_selection"
                self.agent_selection = self._agent_selector.next()

    def _handle_counter_phase(self, player, action):
        # In counter phase, players can block or pass
        # action == PASS means no block
        # Otherwise, block must correspond to legal counter card

        responders = [a for a in self.agents if a != self.pending_player.name and self.players[self.agent_name_mapping[a]].alive]
        if not responders:
            # No blockers, apply action
            self._apply_action()
            self.phase = "action_selection"
            self.agent_selection = self._agent_selector.next()
            return

        # Only first player who wants to counter can act
        if self.counteraction_player is None:
            # Wait for player to counter or pass
            # For simplicity, the agent_selection is set to the responder in order
            # Let's cycle responders
            current_responder = responders[0]
            if player.name != current_responder:
                return

            if action == Action.PASS.value:
                # Pass to next possible blocker or apply action
                responders.pop(0)
                if not responders:
                    self._apply_action()
                    self.phase = "action_selection"
                    self.agent_selection = self._agent_selector.next()
                else:
                    self.agent_selection = responders[0]
            else:
                # Check if action corresponds to a block card claim
                block_cards = possible_counters(self.pending_action)
                claimed_card = None
                # action encodes "block with which card"? We map STEAL (6), TAX(3) etc to counter cards?
                # For simplicity: map actions 0-6 for main actions, PASS=7, so we'll accept counter block only with PASS or PASS=7, otherwise interpret action as block card index:
                # We'll accept: 0=DUKE,1=ASSASSIN,... so if action <5 => block card
                if action < len(Card):
                    claimed_card = Card(action)
                    if claimed_card in block_cards:
                        self.counteraction_player = player
                        self.counteraction_card = claimed_card
                        # Start counter challenge phase
                        self.phase = "counter_challenge"
                        self.counter_challenge_responders = [a for a in self.agents if a != player.name and self.players[self.agent_name_mapping[a]].alive]
                        self.counter_challenge_index = 0
                        if not self.counter_challenge_responders:
                            # No one to challenge counter, counter succeeds
                            self.phase = "action_selection"
                            self.agent_selection = self._agent_selector.next()
                        else:
                            self.agent_selection = self.counter_challenge_responders[0]
                    else:
                        # Invalid block card: pass
                        responders.pop(0)
                        if not responders:
                            self._apply_action()
                            self.phase = "action_selection"
                            self.agent_selection = self._agent_selector.next()
                        else:
                            self.agent_selection = responders[0]
                else:
                    # Invalid action, treat as pass
                    responders.pop(0)
                    if not responders:
                        self._apply_action()
                        self.phase = "action_selection"
                        self.agent_selection = self._agent_selector.next()
                    else:
                        self.agent_selection = responders[0]
        else:
            # Waiting for challenge to counteraction, not counter phase
            pass

    def _handle_counter_challenge_phase(self, player, action):
        # Other players can challenge the counteraction claim
        if not self.counter_challenge_responders:
            # No challengers, counter stands
            self.phase = "action_selection"
            self.agent_selection = self._agent_selector.next()
            return

        challenger_name = self.counter_challenge_responders[self.counter_challenge_index]
        if player.name != challenger_name:
            return

        if action == Action.PASS.value:
            # Pass to next challenger or apply block
            self.counter_challenge_index += 1
            if self.counter_challenge_index >= len(self.counter_challenge_responders):
                # Counter stands, action blocked, action fails
                self.phase = "action_selection"
                self.agent_selection = self._agent_selector.next()
            else:
                self.agent_selection = self.counter_challenge_responders[self.counter_challenge_index]
        else:
            # Challenge counteraction claim
            claimant = self.counteraction_player
            challenger = player
            claimed_card = self.counteraction_card

            if claimed_card in claimant.cards:
                # Claimant proves claim → challenger loses influence
                lost_card = challenger.lose_influence()
                # Claimant exchanges revealed card with deck
                claimant.cards.remove(claimed_card)
                self.deck.append(claimed_card)
                random.shuffle(self.deck)
                claimant.cards.append(self.deck.pop())
                # Counter stands → action blocked → phase ends
                self.phase = "action_selection"
                self.agent_selection = self._agent_selector.next()
            else:
                # Claimant lied → claimant loses influence → action succeeds
                lost_card = claimant.lose_influence()
                self._apply_action()
                self.phase = "action_selection"
                self.agent_selection = self._agent_selector.next()

    def _handle_resolution_phase(self):
        # Placeholder if needed
        pass

    def _apply_action(self):
        # Apply the pending action effect
        p = self.pending_player
        target = self.pending_target
        action = self.pending_action

        if action == Action.TAX.value:
            p.coins += 3
        elif action == Action.ASSASSINATE.value:
            if p.coins >= 3 and target is not None:
                p.coins -= 3
                target.lose_influence()
        elif action == Action.EXCHANGE.value:
            # For simplicity, player draws 2 cards, chooses which 2 to keep - here just replace random
            new_cards = [self.deck.pop(), self.deck.pop()]
            # Replace player's cards randomly for now
            self.deck.extend(p.cards)
            random.shuffle(self.deck)
            p.cards = new_cards
        elif action == Action.STEAL.value:
            if target is not None and target.coins >= 2:
                stolen = 2
                target.coins -= stolen
                p.coins += stolen
            elif target is not None and target.coins == 1:
                stolen = 1
                target.coins -= stolen
                p.coins += stolen
        elif action == Action.FOREIGN_AID.value:
            p.coins += 2
        elif action == Action.INCOME.value:
            p.coins += 1

        # Reset pending action after applying
        self.pending_action = None
        self.pending_player = None
        self.pending_target = None
        self.claimed_card = None

    def _choose_target(self, player):
        # Choose first alive other player for simplicity
        for p in self.players:
            if p != player and p.alive:
                return p
        return None

    def _legal_actions(self, agent):
        idx = self.agent_name_mapping[agent]
        player = self.players[idx]

        actions = []
        # Simplified legality
        actions.append(Action.INCOME.value)
        actions.append(Action.FOREIGN_AID.value)
        if player.coins >= 7:
            actions.append(Action.COUP.value)
        else:
            actions.append(Action.TAX.value)
            if player.coins >= 3:
                actions.append(Action.ASSASSINATE.value)
            actions.append(Action.EXCHANGE.value)
            actions.append(Action.STEAL.value)
        actions.append(Action.PASS.value)  # for passing in challenge/counter phases
        return actions

    def render(self, mode='human'):
        for i, p in enumerate(self.players):
            print(f"{p.name} - Coins: {p.coins} - Cards: {[c.name for c in p.cards]} - Alive: {p.alive}")
        print(f"Phase: {self.phase}")
        if self.phase != "action_selection":
            print(f"Pending Action: {Action(self.pending_action).name if self.pending_action is not None else None} by {self.pending_player.name if self.pending_player else None}")
        print(f"Agent to act: {self.agent_selection}")
        print("----")
