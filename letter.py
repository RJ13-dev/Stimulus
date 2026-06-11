class Letter:
    def __init__(self, id, text, hint, cards):
        self.id = id          # Which letter number — 1, 2, 3...
        self.text = text      # The full letter body Eve reads
        self.hint = hint      # e.g. "art", "cooking", "self_care"
        self.cards = cards    # List of exactly 3 Card objects

    def getCards(self,index):
        return self.cards[index] # Returns the card at the given index (0, 1, or 2)
    
    