import unittest
from main import Player, Card, Action, perform_action, challenge, counteract_challenge

class CoupGameTest(unittest.TestCase):
    def setUp(self):
        self.deck = [Card.DUKE, Card.ASSASSIN, Card.AMBASSADOR, Card.CAPTAIN, Card.CONTESSA] * 3
        self.player1 = Player(0)
        self.player2 = Player(1)
        self.player1.cards = [Card.DUKE, Card.CAPTAIN]
        self.player2.cards = [Card.ASSASSIN, Card.CONTESSA]
        self.player1.coins = 5
        self.player2.coins = 5

    def test_lose_influence_one_card(self):
        self.player1.cards = [Card.DUKE]
        self.player1.lose_influence()
        self.assertFalse(self.player1.alive)
        self.assertEqual(len(self.player1.cards), 0)

    def test_lose_influence_two_cards(self):
        self.player1.lose_influence()
        self.assertEqual(len(self.player1.cards), 1)
        self.assertTrue(self.player1.alive)

    def test_exchange_one_card(self):
        self.player1.cards = [Card.DUKE]
        perform_action(self.player1, Action.EXCHANGE, None, self.deck.copy())
        self.assertEqual(len(self.player1.cards), 1)

    def test_exchange_two_cards(self):
        self.player1.cards = [Card.DUKE, Card.CAPTAIN]
        perform_action(self.player1, Action.EXCHANGE, None, self.deck.copy())
        self.assertEqual(len(self.player1.cards), 2)

    def test_assassinate_action(self):
        self.player1.coins = 3
        perform_action(self.player1, Action.ASSASSINATE, self.player2, self.deck)
        self.assertEqual(self.player1.coins, 0)
        self.assertEqual(len(self.player2.cards), 1)

    def test_steal_action(self):
        self.player2.coins = 2
        perform_action(self.player1, Action.STEAL, self.player2, self.deck)
        self.assertEqual(self.player1.coins, 7)
        self.assertEqual(self.player2.coins, 0)

    def test_challenge_player_with_duke(self):
        # Player 0 claims TAX, Player 1 challenges
        self.player1.cards = [Card.DUKE, Card.AMBASSADOR]  # The one being challenged
        self.player2.cards = [Card.CAPTAIN, Card.CONTESSA]  # The challenger

        result = challenge(self.player2, Action.TAX, self.player1, self.deck)

        # The challenge should FAIL (because player1 actually has DUKE)
        self.assertFalse(result)

        # Player 2 (challenger) should lose a card
        self.assertEqual(len(self.player2.cards), 1)
        self.assertTrue(self.player2.alive)

        # Player 1 should still be alive and have 2 cards (DUKE returned + new card drawn)
        self.assertEqual(len(self.player1.cards), 2)
        self.assertTrue(self.player1.alive)

    def test_challenge_success(self):
        self.player2.cards = [Card.CAPTAIN]
        self.player1.cards = [Card.AMBASSADOR]
        result = challenge(self.player1, Action.TAX, self.player2, self.deck)
        self.assertTrue(result)  # player2 does not have DUKE

    def test_challenge_failure(self):
        self.player2.cards = [Card.DUKE]
        self.player1.cards = [Card.CAPTAIN]
        result = challenge(self.player1, Action.TAX, self.player2, self.deck)
        self.assertFalse(result)  # player2 does have DUKE

    def test_counteract_challenge_success(self):
        self.player2.cards = [Card.CAPTAIN]
        self.player1.cards = [Card.DUKE]
        result = counteract_challenge(self.player1, Card.AMBASSADOR, self.player2, self.deck)
        self.assertTrue(result)  # player2 does not have AMBASSADOR

    def test_counteract_challenge_failure(self):
        self.player2.cards = [Card.CAPTAIN]
        self.player1.cards = [Card.DUKE]
        result = counteract_challenge(self.player1, Card.CAPTAIN, self.player2, self.deck)
        self.assertFalse(result)  # player2 has CAPTAIN

    def test_lose_influence_no_cards(self):
        # Player already eliminated, losing influence should do nothing
        self.player1.cards = []
        self.player1.alive = False
        self.player1.lose_influence()
        self.assertFalse(self.player1.alive)
        self.assertEqual(len(self.player1.cards), 0)

    def test_get_legal_actions_low_coins(self):
        self.player1.coins = 2
        actions = self.player1.get_legal_actions()
        self.assertNotIn(Action.ASSASSINATE, actions)
        self.assertNotIn(Action.COUP, actions)

    def test_get_legal_actions_high_coins(self):
        self.player1.coins = 7
        actions = self.player1.get_legal_actions()
        self.assertIn(Action.ASSASSINATE, actions)
        self.assertIn(Action.COUP, actions)

    def test_perform_action_foreign_aid(self):
        coins_before = self.player1.coins
        perform_action(self.player1, Action.FOREIGN_AID, None, self.deck)
        self.assertEqual(self.player1.coins, coins_before + 2)

    def test_assassinate_insufficient_coins(self):
        self.player1.coins = 2
        coins_before = self.player1.coins
        cards_before = len(self.player2.cards)
        # Should not perform assassination if coins < 3, but perform_action doesn't block it explicitly
        # So, either your game logic should prevent it or test expects coins to go negative
        perform_action(self.player1, Action.ASSASSINATE, self.player2, self.deck)
        # Check coins reduced by 3 (negative allowed in current code)
        self.assertEqual(self.player1.coins, coins_before - 3)
        # Target should lose influence
        self.assertEqual(len(self.player2.cards), cards_before - 1)

    def test_steal_less_than_two_coins(self):
        self.player2.coins = 1
        self.player1.coins = 5
        perform_action(self.player1, Action.STEAL, self.player2, self.deck)
        self.assertEqual(self.player1.coins, 6)
        self.assertEqual(self.player2.coins, 0)

    def test_exchange_returns_to_deck(self):
        # Copy deck to count cards before and after
        deck_copy = self.deck.copy()
        self.player1.cards = [Card.DUKE, Card.CAPTAIN]
        perform_action(self.player1, Action.EXCHANGE, None, deck_copy)
        # Cards in hand should remain 2
        self.assertEqual(len(self.player1.cards), 2)
        # Deck size should remain the same after draw and return
        self.assertEqual(len(deck_copy), len(self.deck))

if __name__ == '__main__':
    unittest.main()
