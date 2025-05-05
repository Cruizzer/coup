class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.coins = 2
        self.cards = []
        self.lost_cards = []
        self.alive = True

    def is_alive(self):
        return len(self.cards) > 0

    def lose_influence(self, card_to_lose=None):
        if card_to_lose and card_to_lose in self.cards:
            self.cards.remove(card_to_lose)
        else:
            self.cards.pop()
        if not self.cards:
            self.alive = False