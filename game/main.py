from enum import Enum
import random

class Card(Enum):
    DUKE = 0
    ASSASSIN = 1
    AMBASSADOR = 2
    CAPTAIN = 3
    CONTESSA = 4

class Action(Enum):
    INCOME = 5
    FOREIGN_AID = 6
    COUP = 7
    TAX = 8
    ASSASSINATE = 9
    EXCHANGE = 10
    STEAL = 11

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.coins = 2
        self.cards = []
        self.alive = True

    def lose_influence(self):
        if not self.cards:
            return
        lost_card = self.cards.pop() if len(self.cards) == 1 else self.cards.pop(random.randint(0, 1))
        print(f"Player {self.id} loses {lost_card.name}")
        print("Remaining cards:", end=" ")
        print_cards(self.cards)
        if not self.cards:
            self.alive = False
            print(f"Player {self.id} has died.\n")

    def get_legal_actions(self):
        actions = list(Action)
        if self.coins < 3:
            actions = [a for a in actions if a != Action.ASSASSINATE]
        if self.coins < 7:
            actions = [a for a in actions if a != Action.COUP]
        return actions

def print_cards(cards: list, debug=False):
    for card in cards:
        print(card.name, end=" ")
    print()

def challenge(challenger: Player, action: Action, target: Player, deck: list):
    claim_card = {
        Action.TAX: Card.DUKE,
        Action.EXCHANGE: Card.AMBASSADOR,
        Action.ASSASSINATE: Card.ASSASSIN,
        Action.STEAL: Card.CAPTAIN
    }.get(action, None)

    if not claim_card:
        return False

    print(f"[DEBUG] Challenged player's cards: {target.cards}, Claim: {claim_card}")
    print(f"Player {challenger.id} challenges Player {target.id}'s claim of {claim_card.name}")

    if claim_card in target.cards:
        print(f"Challenge failed! Player {target.id} had {claim_card.name}.")
        challenger.lose_influence()
        target.cards.remove(claim_card)
        deck.append(claim_card)
        random.shuffle(deck)
        target.cards.append(deck.pop())
        return False
    else:
        print(f"Challenge successful! Player {target.id} did not have {claim_card.name}.")
        target.lose_influence()
        return True

def counteract(action: Action):
    if action == Action.ASSASSINATE:
        return Card.CONTESSA
    elif action == Action.STEAL:
        return random.choice([Card.CAPTAIN, Card.AMBASSADOR])
    elif action == Action.FOREIGN_AID:
        return Card.DUKE
    return None

def counteract_challenge(challenger: Player, claim_card: Card, target: Player, deck: list):
    if claim_card in target.cards:
        print(f"Challenge failed! Player {target.id} had {claim_card.name}.")
        challenger.lose_influence()
        target.cards.remove(claim_card)
        deck.append(claim_card)
        random.shuffle(deck)
        target.cards.append(deck.pop())
        return False
    else:
        print(f"Challenge successful! Player {target.id} did not have {claim_card.name}.")
        target.lose_influence()
        return True

def perform_action(player: Player, action: Action, target: Player, deck: list):
    print(f"Player {player.id} performs {action.name}", end="")
    if target:
        print(f" on Player {target.id}", end="")
    print(f" | Coins: {player.coins}")

    if action == Action.FOREIGN_AID:
        player.coins += 2
    elif action == Action.TAX:
        player.coins += 3
    elif action == Action.ASSASSINATE:
        player.coins -= 3
        target.lose_influence()
    elif action == Action.STEAL:
        stolen = min(2, target.coins)
        target.coins -= stolen
        player.coins += stolen
    elif action == Action.EXCHANGE:
        num_to_draw = 2 if len(player.cards) == 2 else 1
        drawn = [deck.pop() for _ in range(num_to_draw)]
        print(f"Player {player.id} draws {len(drawn)} card(s): {[c.name for c in drawn]}")
        combined = player.cards + drawn
        random.shuffle(combined)
        num_to_keep = len(player.cards)
        player.cards = combined[:num_to_keep]
        returned = combined[num_to_keep:]
        deck.extend(returned)
        random.shuffle(deck)
        print(f"Player {player.id}'s new hand after Exchange:")
        print_cards(player.cards)
    print("----")

def main():
    num_players = 3
    deck = [card for card in Card] * 3
    random.shuffle(deck)

    players = [Player(i) for i in range(num_players)]
    for player in players:
        player.cards = [deck.pop(), deck.pop()]
        print(f"Player {player.id} starts with:")
        print_cards(player.cards)
    print()

    current_player_idx = 0

    while True:
        alive_players = [p for p in players if p.alive]
        if len(alive_players) == 1:
            print(f"Player {alive_players[0].id} wins!")
            return alive_players[0].id

        current_player = players[current_player_idx]
        if not current_player.alive:
            current_player_idx = (current_player_idx + 1) % num_players
            continue

        action = random.choice(current_player.get_legal_actions())
        print(f"Player {current_player.id} chose: {action.name}")

        target = None
        if action in [Action.COUP, Action.ASSASSINATE, Action.STEAL]:
            targets = [p for p in players if p != current_player and p.alive]
            if targets:
                target = random.choice(targets)

        if action == Action.INCOME:
            current_player.coins += 1
            current_player_idx = (current_player_idx + 1) % num_players
            continue
        elif action == Action.COUP:
            current_player.coins -= 7
            target.lose_influence()
            current_player_idx = (current_player_idx + 1) % num_players
            continue

        challenger = None
        if random.random() < 0.3:
            challengers = [p for p in players if p != current_player and p.alive]
            if challengers:
                challenger = random.choice(challengers)

        successful_challenge = False
        if challenger:
            successful_challenge = challenge(challenger, action, current_player, deck)
            if successful_challenge:
                current_player_idx = (current_player_idx + 1) % num_players
                continue

        counteractor = None
        counteract_challenger = None
        counter_claim = None
        if action in [Action.FOREIGN_AID, Action.ASSASSINATE, Action.STEAL] and random.random() < 0.3:
            if action == Action.FOREIGN_AID:
                counteractor = random.choice([p for p in players if p != current_player and p.alive])
            elif target and target.alive:
                counteractor = target

            if counteractor:
                counter_claim = counteract(action)
                print(f"Player {counteractor.id} counteracts with {counter_claim.name}")
                if random.random() < 0.5:
                    challengers = [p for p in players if p != counteractor and p.alive]
                    if challengers:
                        counteract_challenger = random.choice(challengers)

        if counteractor and counteract_challenger:
            print(f"Player {counteract_challenger.id} challenges counteraction!")
            if counteract_challenge(counteract_challenger, counter_claim, counteractor, deck):
                perform_action(current_player, action, target, deck)
        elif not counteractor:
            perform_action(current_player, action, target, deck)

        current_player_idx = (current_player_idx + 1) % num_players

# Run the game
main()

# players = [0, 0, 0]
# for i in range(100000):
#     player = main()
#     players[player] += 1
# print(players)