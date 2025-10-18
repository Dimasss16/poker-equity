import unittest
from src.deck import Card, Deck


class TestCard(unittest.TestCase):

    def test_card_creation(self):
        card = Card('A', 's')
        self.assertEqual(card.rank, 'A')
        self.assertEqual(card.suit, 's')

    def test_card_string_representation(self):
        s1 = str(Card('A', 's'))
        self.assertIn('A', s1)
        self.assertIn('♠', s1)

        s2 = str(Card('K', 'h'))
        self.assertIn('K', s2)
        self.assertIn('♥', s2)

    def test_card_equality(self):
        card1 = Card('A', 's')
        card2 = Card('A', 's')
        self.assertEqual(card1, card2)


class TestDeck(unittest.TestCase):

    def test_deck_initialization(self):
        deck = Deck()
        self.assertEqual(len(deck), 52)
        self.assertEqual(deck.cards_remaining(), 52)
        self.assertFalse(deck.is_empty())

    def test_deck_contains_all_cards(self):
        deck = Deck()
        cards = [deck.deal_one() for _ in range(52)]

        self.assertEqual(len(cards), 52)
        self.assertEqual(len(set(cards)), 52)

        ranks = [c.rank for c in cards]
        suits = [c.suit for c in cards]
        self.assertEqual(ranks.count('A'), 4)
        self.assertEqual(suits.count('s'), 13)

    def test_deal_one_removes_card(self):
        deck = Deck()
        initial_count = len(deck)

        card = deck.deal_one()

        self.assertIsInstance(card, Card)
        self.assertEqual(len(deck), initial_count - 1)
        self.assertEqual(deck.cards_remaining(), 51)

    def test_deal_all_cards(self):
        deck = Deck()

        for i in range(52):
            deck.deal_one()
            self.assertEqual(len(deck), 51 - i)

        self.assertTrue(deck.is_empty())
        self.assertEqual(len(deck), 0)

    def test_deal_from_empty_deck_raises_error(self):
        deck = Deck()

        # Deal all cards
        for _ in range(52):
            deck.deal_one()

        # Try to deal one more
        with self.assertRaisesRegex(IndexError, r"Cannot deal from an empty deck"):
            deck.deal_one()

    def test_shuffle_changes_order(self):
        deck1 = Deck()
        deck2 = Deck()

        card1_before = deck1.deal_one()
        card2_before = deck2.deal_one()
        self.assertEqual(card1_before, card2_before)

        deck1.reset()
        deck2.reset()

        deck1.shuffle(seed=42)
        deck2.shuffle(seed=99)

        # First cards should now differ
        card1_after = deck1.deal_one()
        card2_after = deck2.deal_one()
        self.assertNotEqual(card1_after, card2_after)

    def test_shuffle_with_seed_is_reproducible(self):
        deck1 = Deck()
        deck1.shuffle(seed=42)
        cards1 = [deck1.deal_one() for _ in range(5)]

        deck2 = Deck()
        deck2.shuffle(seed=42)
        cards2 = [deck2.deal_one() for _ in range(5)]

        self.assertEqual(cards1, cards2)

    def test_reset_restores_full_deck(self):
        deck = Deck()

        deck.deal_one()
        deck.deal_one()
        deck.deal_one()
        self.assertEqual(len(deck), 49)

        deck.reset()
        self.assertEqual(len(deck), 52)
        self.assertFalse(deck.is_empty())

    def test_deck_string_representation(self):
        deck = Deck()
        self.assertIn("52", str(deck))

        deck.deal_one()
        self.assertIn("51", str(deck))


if __name__ == '__main__':
    unittest.main()
