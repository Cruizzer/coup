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

    def lose_influence(self, players: list, current_player_idx: int):
        if len(self.cards) == 1:
            lost_card = self.cards.pop()
        else:
            random_number = random.randint(0, 1)
            lost_card = self.cards.pop(random_number)
            
        print(f"Player {self.id} loses {Card(lost_card).name}. Remaining hand:")
        print_cards(self.cards)
        
        if not self.cards:
            players[self.id] = -1
            print(f"Player {self.id} has died.")

    def get_legal_actions(self):
        actions = list(Action)
        if self.coins < 3:
            actions.remove(Action.ASSASSINATE)
        if self.coins < 7:
            actions.remove(Action.COUP)
        return actions
    
        
        


def print_cards(cards: list, debug=False):
    for i in range(len(cards)):
        if debug:
            print(Card(cards[i]).name, end=" ")
        else:
            print(cards[i], end=" ")
    print()
    

def challenge(challenger: Player, action: Action, target: Player, deck:list, current_player_idx: int):
    claim_card = None
    if action == Action.TAX:
        claim_card = Card.DUKE
    elif action == Action.EXCHANGE:
        claim_card = Card.AMBASSADOR
    elif action == Action.ASSASSINATE:
        claim_card = Card.ASSASSIN
    elif action == Action.STEAL:
        claim_card = Card.CAPTAIN

    print(f"Player {challenger.id} challenges Player {target.id}'s claim of {Card(claim_card).name}")
    if claim_card in target.cards:
        print(f"Challenge failed! Player {target.id} had {claim_card}.")
        challenger.lose_influence(deck, current_player_idx)
        random.shuffle(target.cards)
        card = target.cards.pop()
        deck.append(card)
        random.shuffle(deck)
        target.cards.append(deck.pop())
        return False
    else:
        print(f"Challenge successful! Player {target.id} did not have {claim_card}.")
        target.lose_influence(deck, current_player_idx)
        random.shuffle(challenger.cards)
        card = challenger.cards.pop()
        deck.append(card)
        random.shuffle(deck)
        challenger.cards.append(deck.pop())
        return True
    

def counteract(action: Action):
    counterclaim_card = None
    if action == Action.ASSASSINATE:
        counterclaim_card = Card.CONTESSA
    elif action == Action.STEAL:
        counterclaim_card = random.choice([Card.CAPTAIN, Card.AMBASSADOR])

    return counterclaim_card



def counteract_challenge(challenger: Player, claim_card: Card, target: Player, deck:list, current_player_idx: int):
    if claim_card in target.cards:
        print(f"Challenge failed! Player {target} had {claim_card}.")
        challenger.lose_influence(deck, current_player_idx)
        random.shuffle(target.cards)
        card = target.cards.pop()
        deck.append(card)
        random.shuffle(deck)
        target.cards.append(deck.pop())
        return False
    else:
        print(f"Challenge successful! Player {target} did not have {claim_card}.")
        target.lose_influence(deck, current_player_idx)
        random.shuffle(challenger.cards)
        card = challenger.cards.pop()
        deck.append(card)
        random.shuffle(deck)
        challenger.cards.append(deck.pop())
        return True


def perform_action(player: Player, action: Action, target: Player, deck: list, current_player_idx: int):

        if target:
            print(f"Player {player.id} performs {action}" + 
                (f" on Player {target.id}") + 
                f" | Coins: {player.coins}")
        else:
            print(f"Player {player.id} performs {action}" + 
                f" | Coins: {player.coins}")


        if action == Action.FOREIGN_AID:
            player.coins += 2
        elif action == Action.TAX:
            player.coins += 3
        elif action == Action.ASSASSINATE:
            player.coins -= 3
            target.lose_influence(deck, current_player_idx)
        elif action == Action.STEAL:
            stolen = min(2, target.coins)
            target.coins -= stolen
            player.coins += stolen
        elif action == Action.EXCHANGE:
            num_to_draw = 2 if len(player.cards) == 2 else 1
            drawn = [deck.pop() for _ in range(num_to_draw)]
            print(f"Player {player.id} draws {drawn} using Ambassador.")

            combined = player.cards + drawn
            random.shuffle(combined)
            player.cards = combined[:2]

            returned = combined[2:]
            deck += returned
            random.shuffle(deck)

            # Output the player's hand after the exchange
            print(f"Player {player.id}'s new hand after exchange:")
            print_cards(player.cards)


        print("----")


def main():
    num_players = 3
    deck = [0, 1, 2, 3, 4] * 3
    random.shuffle(deck)
    players = [Player(i) for i in range(num_players)]

    # Initialise hands
    for i in range(num_players):
        players[i].cards = [deck.pop(), deck.pop()]
        print(f"Player {i} starts with:")
        print_cards(players[i].cards, 1)
    print()

    current_player_idx = 0
    is_ended = 0

    # Game loop: Action, callout, counteraction, callout, effect
    while not is_ended:

        if sum(x != -1 for x in players) == 1:
            is_ended = True
            print(f"Player {current_player_idx - 1} won")
            continue

        if players[current_player_idx] == -1:
            current_player_idx += 1
            continue

        current_player = players[current_player_idx]
        chosen_action = random.choice(current_player.get_legal_actions())
        print(f"Player {current_player_idx} chose: {Action(chosen_action).name}")
        
        # Select a target player.
        target_player = None
        if chosen_action == Action.COUP or chosen_action == Action.ASSASSINATE or chosen_action == Action.STEAL:
            other_players = [p for p in players if p != current_player and players[p.id] != -1]
            target_player = random.choice(other_players)


        if chosen_action == Action.INCOME:
            current_player.coins += 1
            current_player_idx = (current_player_idx + 1) % num_players
            continue
        elif chosen_action == Action.COUP:
            current_player.coins -= 7
            target_player.lose_influence(players, current_player_idx)
            current_player_idx = (current_player_idx + 1) % num_players
            continue

        challenger = None
        successful_challenge = None

        # 30% chance of challenging
        if random.random() < 0.3:
            other_players = [p for p in players if p != current_player and players[p.id] != -1]
            challenger = random.choice(other_players)

        if not chosen_action == Action.FOREIGN_AID:
            if challenger:
                successful_challenge = challenge(challenger, chosen_action, current_player, deck)


        successful_counteract_challenge = None
        counteract_player = None
        counteract_challenger = None
        
        # 30% chance of counteracting. (Maybe specify what actions to reduce computational overhead).
        if random.random() < 0.3:
            # Only foreign aid can be counteracted by anyone (even people not included in the action).
            if chosen_action == Action.FOREIGN_AID:
                other_players = [p for p in players if p != target_player and players[p.id] != -1]
                if not other_players:
                    continue
                counteract_player = random.choice(other_players)
            else:
                counteract_player = target_player

            # 60% chance of challenging a counteraction. Anyone can challenge
            if random.random() < 0.6:
                other_players = [p for p in players if p != target_player and players[p.id] != -1]
                if not other_players:
                    continue
                counteract_challenger = random.choice(other_players)


        # 30% chance of counteracting either foreign aid, steal, or assassinate.
        if counteract_player:
            if chosen_action == Action.FOREIGN_AID:
                # Anyone can counteract with Duke and anyone can challenge the counteract.
                print(f"Player {counteract_player.id} counteracted with Duke!")

                if counteract_challenger:
                    print(f"Player {counteract_challenger.id} is challenging the Duke claim!")
                    successful_counteract_challenge = counteract_challenge(counteract_challenger, Card.DUKE, counteract_player, deck)

            elif chosen_action == Action.STEAL or chosen_action == Action.ASSASSINATE:
                # Only the targetted player can counteract but anyone can challenge the counteract.
                claim_card = counteract(chosen_action)
                print(f"Player {target_player.id} counteracted with {claim_card}")

                if counteract_challenger:
                    print(f"Player {counteract_challenger.id} is challenging the {claim_card} claim!")
                    successful_counteract_challenge = counteract_challenge(counteract_challenger, claim_card, counteract_player, deck)

        if not successful_challenge and (not counteract_player or successful_counteract_challenge):
            perform_action(current_player, chosen_action, target_player, deck)
            current_player_idx = (current_player_idx + 1) % num_players
        
    

main()

