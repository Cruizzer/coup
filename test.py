# Full base game engine for Coup with bluffing and blocking
import random
from collections import deque

class Card:
    DUKE = "Duke"
    ASSASSIN = "Assassin"
    CAPTAIN = "Captain"
    AMBASSADOR = "Ambassador"
    CONTESSA = "Contessa"
    ALL_CARDS = [DUKE, ASSASSIN, CAPTAIN, AMBASSADOR, CONTESSA]

class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.coins = 2
        self.cards = []
        self.lost_cards = []
        self.alive = True

    def is_alive(self):
        return self.alive

    def lose_influence(self, card_to_lose=None):
        if card_to_lose and card_to_lose in self.cards:
            self.cards.remove(card_to_lose)
        elif self.cards:
            self.cards.pop()
        if not self.cards:
            self.alive = False
        print(f"Player {self.id} loses a card. Remaining hand: {self.cards}")


class Action:
    INCOME = "income"
    FOREIGN_AID = "foreign_aid"
    COUP = "coup"
    TAX = "tax"
    ASSASSINATE = "assassinate"
    STEAL = "steal"
    EXCHANGE = "exchange"
    BLOCK_FOREIGN_AID = "block_foreign_aid"
    BLOCK_STEAL = "block_steal"
    BLOCK_ASSASSINATE = "block_assassinate"
    CHALLENGE = "challenge"

    PRIMARY_ACTIONS = [INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE]
    BLOCK_ACTIONS = [BLOCK_FOREIGN_AID, BLOCK_STEAL, BLOCK_ASSASSINATE]

class GameState:
    def __init__(self, num_players):
        self.num_players = num_players
        self.players = [Player(i) for i in range(num_players)]
        self.deck = self._init_deck()
        self.current_player_idx = 0
        self.action_stack = deque()
        self.history = []
        self._deal_initial_cards()

    def _init_deck(self):
        deck = Card.ALL_CARDS * 3
        random.shuffle(deck)
        return deck

    def _deal_initial_cards(self):
        for player in self.players:
            player.cards = [self.deck.pop(), self.deck.pop()]

    def get_current_player(self):
        return self.players[self.current_player_idx]

    def get_alive_players(self):
        return [p for p in self.players if p.is_alive()]

    def next_player(self):
        start_idx = self.current_player_idx
        while True:
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players
            if self.players[self.current_player_idx].is_alive():
                break
            if self.current_player_idx == start_idx:
                break

    def is_game_over(self):
        return len(self.get_alive_players()) == 1

    def get_winner(self):
        if self.is_game_over():
            return self.get_alive_players()[0].id
        return None

    def challenge(self, challenger_id, target_id, target_claim):
        target = self.players[target_id]
        challenger = self.players[challenger_id]
        print(f"Player {challenger_id} challenges Player {target_id}'s claim of {target_claim}.")
        if target_claim in target.cards:
            print(f"Challenge failed! Player {target_id} had {target_claim}.")
            challenger.lose_influence()
            try: # This except should be removed since it should be impossible (can only happen if self-challenge?)
                target.cards.remove(target_claim)
            except ValueError:
                print(f"WARNING: {target_claim} not in Player {target_id}'s hand during challenge resolution.")
                return False
            self.deck.append(target_claim)
            random.shuffle(self.deck)
            target.cards.append(self.deck.pop())
            return False
        else:
            print(f"Challenge successful! Player {target_id} did not have {target_claim}.")
            target.lose_influence()
            return True

    # def block_action(self, blocker_id, action, challenger_id=None):
    #     required_card = None
    #     if action == Action.FOREIGN_AID:
    #         required_card = Card.DUKE
    #     elif action == Action.ASSASSINATE:
    #         required_card = Card.CONTESSA
    #     elif action == Action.STEAL:
    #         required_card = Card.CAPTAIN

    #     if challenger_id is not None:
    #         return self.challenge(challenger_id, blocker_id, required_card)

    #     print(f"Player {blocker_id} blocks action {action} using {required_card}.")
    #     return True

    def perform_action(self, player_id, action, target_id=None):
        player = self.players[player_id]
        if not player.is_alive():
            return False

        if action in Action.PRIMARY_ACTIONS:
            print(f"Player {player_id} performs {action}" + 
                (f" on Player {target_id}" if target_id is not None else "") + 
                f" | Coins: {player.coins}")

        # self.history.append((challenged_by, Action.CHALLENGE, player_id, claim_card))
        # self.next_player()


        # print(f"Player {player_id} performs {action}" + (f" on Player {target_id}" if target_id is not None else ""))

        if action == Action.INCOME:
            player.coins += 1
        elif action == Action.FOREIGN_AID:
            player.coins += 2
        elif action == Action.COUP and target_id is not None and player.coins >= 7:
            player.coins -= 7
            self.players[target_id].lose_influence()
        elif action == Action.TAX:
            player.coins += 3
        elif action == Action.ASSASSINATE and target_id is not None and player.coins >= 3:
            player.coins -= 3
            self.players[target_id].lose_influence()
        elif action == Action.STEAL and target_id is not None:
            target = self.players[target_id]
            stolen = min(2, target.coins)
            target.coins -= stolen
            player.coins += stolen
        elif action == Action.EXCHANGE:
            num_to_draw = 2 if len(player.cards) == 2 else 1
            drawn = [self.deck.pop() for _ in range(num_to_draw)]
            print(f"Player {player_id} draws {drawn} using Ambassador.")

            combined = player.cards + drawn
            random.shuffle(combined)
            player.cards = combined[:2]

            returned = combined[2:]
            self.deck += returned
            random.shuffle(self.deck)

            # Output the player's hand after the exchange
            print(f"Player {player_id}'s new hand after exchange: {player.cards}")


        print("----")

        return True

    def get_legal_actions(self, player_id):
        player = self.players[player_id]
        if not player.is_alive():
            return []

        actions = [Action.INCOME, Action.FOREIGN_AID, Action.TAX, Action.EXCHANGE]

        if player.coins >= 7:
            actions.append(Action.COUP)

        if player.coins >= 3:
            actions.append(Action.ASSASSINATE)

        # Only allow STEAL if there's a valid target with at least 1 coin
        steal_targets = [
            p for p in self.players
            if p.id != player_id and p.is_alive() and p.coins >= 2
        ]
        if steal_targets:
            actions.append(Action.STEAL)

        return actions
    
# def challenge(self, challenger_id, target_id, target_claim):
#     target = self.players[target_id]
#     challenger = self.players[challenger_id]
#     print(f"Player {challenger_id} challenges Player {target_id}'s claim of {target_claim}.")
#     if target_claim in target.cards:
#         print(f"Challenge failed! Player {target_id} had {target_claim}.")
#         challenger.lose_influence()
#         try: # This except should be removed since it should be impossible (can only happen if self-challenge?)
#             target.cards.remove(target_claim)
#         except ValueError:
#             print(f"WARNING: {target_claim} not in Player {target_id}'s hand during challenge resolution.")
#             return True
#         self.deck.append(target_claim)
#         random.shuffle(self.deck)
#         target.cards.append(self.deck.pop())
#         return True
#     else:
#         print(f"Challenge successful! Player {target_id} did not have {target_claim}.")
#         target.lose_influence()
#         return False

def block_foreign_aid(blocker_id, target_id):
    print(f"Player {blocker_id} blocks foreign aid from {target_id} using Duke.")
    return


def counteract(counter_card_claim, player_id):
    print(f"Player {player_id} counteracts with: {counter_card_claim}")
    return


def simulate_random_game(num_players=3):
    game = GameState(num_players)
    print("Starting a new game of Coup")
    for p in game.players:
        print(f"Player {p.id} starts with: {p.cards}")

    while not game.is_game_over():
        player = game.get_current_player()
        player_id = player.id
        legal_actions = game.get_legal_actions(player_id)
        action = random.choice(legal_actions)

        print(legal_actions)

        target_id = None
        if action in [Action.ASSASSINATE, Action.STEAL, Action.COUP]:
            if action == Action.STEAL:
                targets = [p.id for p in game.players if p.id != player_id and p.is_alive() and p.coins >= 2]
            else:
                targets = [p.id for p in game.players if p.id != player_id and p.is_alive()]
            if targets:
                target_id = random.choice(targets)
            else:
                # Skip this action if no valid targets
                continue

        # Tax and exchange do not have a target_id, while the other actions do.
        claim_card = None
        if action == Action.TAX:
            claim_card = Card.DUKE
        elif action == Action.EXCHANGE:
            claim_card = Card.AMBASSADOR
        elif action == Action.ASSASSINATE:
            claim_card = Card.ASSASSIN
        elif action == Action.STEAL:
            claim_card = Card.CAPTAIN
            # claim_card = Card.CAPTAIN or Card.AMBASSADOR

        # Above is all good.


        # A challenge is being definde as whether the initial action can go to completion uninterrupted.
        # The only actions in the game that cannot be challenged are income and coup.
        # There is a 30% chance for any action to be challenged, and a random player is picked among all alive.
        challenged_by = None
        challenged_status = 0
        if action != (Action.INCOME or Action.COUP):
            if random.random() < 0.3:
                challengers = [p.id for p in game.players if p.id != player_id and p.is_alive()]
                challenged_by = random.choice(challengers)


        # Foreign aid has a unique interaction since it doesn't require a claim card.
        if challenged_by is not None:
            print(f'Player {player_id} attempts to perform {action}.')
            
            if action == Action.FOREIGN_AID:
                # 30% chance someone calls out the Duke, otherwise foreign aid is just blocked.
                if random.random() < 0.3:
                    duke_challengers = [p.id for p in game.players if p.id != challenged_by and p.is_alive()]
                    duke_challenged_by = random.choice(duke_challengers)

                    # 30% chance that the Duke claim is challenged, otherwise the block just goes through
                    foreign_aid_challenge_status = game.challenge(duke_challenged_by, challenged_by, Card.DUKE)
                    if not foreign_aid_challenge_status:
                        block_foreign_aid(challenged_by, player_id)
                        challenged_status = 1
                else:
                    print(f'Player {challenged_by} blocked foreign aid to {player_id}.')
                    block_foreign_aid(challenged_by, player_id)
                    challenged_status = 1
                    
            else:
                challenged_status = game.challenge(challenged_by, player_id, claim_card)

        # If there is no challenge, then the action goes through the first stage, and now the target must respond.
        # Assassinate and steal are the only actions that can be responded to.
        counteracted_challenge_status = 0

        if action == Action.ASSASSINATE and target_id is not None and random.random() < 0.5:
            # 50% chance the target claims Contessa.
            counteract(Card.CONTESSA, target_id)
            if random.random() < 0.5: # 50% chance someone calls out the Contessa counteract ability.
                challengers = [p.id for p in game.players if p.id != target_id and p.is_alive()]
                challenged_by = random.choice(challengers)
                counteracted_challenge_status = game.challenge(challenged_by, target_id, Card.CONTESSA)
            else:
                counteract(Card.CONTESSA, target_id)
                counteracted_challenge_status = 1

        elif action == Action.STEAL and target_id is not None and random.random() < 0.5:
            if Card.CAPTAIN in player.cards:
                counteract_card = Card.CAPTAIN
            elif Card.AMBASSADOR in player.cards:
                counteract_card = Card.AMBASSADOR
            else:
                counteract_card = random.choice([Card.CAPTAIN, Card.AMBASSADOR])

            if random.random() < 0.5: # 50% chance someone calls out the Captain/Ambassador block.
                challengers = [p.id for p in game.players if p.id != target_id and p.is_alive()]
                challenged_by = random.choice(challengers)
                counteracted_challenge_status = game.challenge(challenged_by, target_id, counteract_card)
            else:
                counteract(counteract_card, target_id)
                counteracted_challenge_status = 1

            


        # For an action to have its effect, the initial challenge, if any, must have failed.
        # Also the counteract challenge, if any, must have also  failed.
        if not challenged_status and not counteracted_challenge_status:
            game.perform_action(player_id, action, target_id)

        game.history.append((player_id, action, target_id))
        game.next_player()
            

        # if action == Action.FOREIGN_AID and random.random() < 0.3:
        #     block_candidates = [p.id for p in game.players if p.id != player_id and p.is_alive()]
        #     if block_candidates:
        #         block_by = random.choice(block_candidates)
        #         challengers = [p.id for p in game.players if p.id != block_by and p.is_alive()]
        #         if challengers and random.random() < 0.5:
        #             challenged_by = random.choice(challengers)



        # Doesn't hurt to check if target_id is not None, even though it shouldn't be because of earlier check.
        # elif action == Action.ASSASSINATE and target_id is not None and random.random() < 0.3:
        #     block_by = target_id
        #     challengers = [p.id for p in game.players if p.id != block_by and p.is_alive()]
        #     if challengers and random.random() < 0.5:
        #         challenged_by = random.choice(challengers)

        # elif action == Action.STEAL and target_id is not None and random.random() < 0.3:
        #     block_by = target_id
        #     challengers = [p.id for p in game.players if p.id != block_by and p.is_alive()]
        #     if challengers and random.random() < 0.5:
        #         challenged_by = random.choice(challengers)

        # elif claim_card and random.random() < 0.3:
        #     challengers = [p.id for p in game.players if p.id != player_id and p.is_alive()]
        #     if challengers:
        #         challenged_by = random.choice(challengers)

        # game.perform_action(player_id, action, target_id, claim_card, block_by, challenged_by)

    print(f"Game over! Winner: Player {game.get_winner()}")

for i in range(1):
    simulate_random_game()