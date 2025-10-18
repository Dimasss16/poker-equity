import unittest
from src.deck import Card, Deck
from src.evaluator import evaluate, handtype, compare


class TestEvaluator(unittest.TestCase):
    def test_evaluate_requires_seven_cards(self):
        with self.assertRaisesRegex(ValueError, r"Expected exactly 7 cards"):
            evaluate([Card('A', 's'), Card('K', 's')])

    def test_straight_flush_highest(self):
        royal = [
            Card('A', 's'), Card('K', 's'), Card('Q', 's'),
            Card('J', 's'), Card('T', 's'), Card('2', 'h'), Card('3', 'h')
        ]
        rank = evaluate(royal)
        self.assertGreater(rank, 130_000_000)  # very high in eval7 scale
        self.assertEqual(handtype(royal), "Straight Flush")  # royals are straight flushes

    def test_pair_beats_high_card(self):
        pair = [
            Card('2', 's'), Card('2', 'h'), Card('A', 'd'),
            Card('K', 's'), Card('Q', 'h'), Card('J', 'c'), Card('9', 'c')
        ]
        high_card = [
            Card('A', 's'), Card('K', 'h'), Card('Q', 'd'),
            Card('J', 's'), Card('9', 'd'), Card('7', 'h'), Card('5', 'd')
        ]
        self.assertGreater(evaluate(pair), evaluate(high_card))
        self.assertEqual(handtype(pair), "Pair")
        self.assertEqual(handtype(high_card), "High Card")

    def test_compare_function(self):
        straight_flush = [
            Card('A', 's'), Card('K', 's'), Card('Q', 's'),
            Card('J', 's'), Card('T', 's'), Card('2', 'h'), Card('3', 'h')
        ]
        pair = [
            Card('A', 'h'), Card('A', 'd'), Card('K', 'c'),
            Card('Q', 'h'), Card('J', 'd'), Card('9', 's'), Card('7', 's')
        ]

        self.assertEqual(compare(straight_flush, pair), -1)  # first wins
        self.assertEqual(compare(pair, straight_flush), 1)   # second wins
        self.assertEqual(compare(straight_flush, straight_flush), 0)  # tie

    def test_compare_royal_vs_straight_flush(self):
        royal_flush = [
            Card('A', 's'), Card('K', 's'), Card('Q', 's'),
            Card('J', 's'), Card('T', 's'), Card('2', 'h'), Card('3', 'h')
        ]
        straight_flush = [
            Card('8', 'h'), Card('7', 'h'), Card('6', 'h'),
            Card('5', 'h'), Card('4', 'h'), Card('9', 's'), Card('7', 's')
        ]

        self.assertEqual(compare(straight_flush, royal_flush), 1)  # second wins
        self.assertEqual(compare(royal_flush, straight_flush), -1)   # first wins
        self.assertEqual(compare(royal_flush, royal_flush), 0)  # tie

    def test_dealt_hands(self):
        deck = Deck()
        deck.shuffle(seed=42)

        hand1 = [deck.deal_one() for _ in range(7)]
        hand2 = [deck.deal_one() for _ in range(7)]

        rank1 = evaluate(hand1)
        rank2 = evaluate(hand2)

        self.assertGreater(rank1, 0)
        self.assertGreater(rank2, 0)

        result = compare(hand1, hand2)
        self.assertIn(result, (-1, 0, 1))


if __name__ == '__main__':
    unittest.main()
