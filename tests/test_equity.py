import unittest
from src.equity import compute_heads_up_equity, compute_equity_vs_hand
from src.utils import parse_hand_class, sample_hand_from_class, get_combo_count
from src.deck import Card


class TestHandClassParsing(unittest.TestCase):
    def test_parse_pair(self):
        r1, r2, suited = parse_hand_class("AA")
        self.assertEqual(r1, 'A')
        self.assertEqual(r2, 'A')
        self.assertIsNone(suited)

        r1, r2, suited = parse_hand_class("22")
        self.assertEqual(r1, '2')
        self.assertEqual(r2, '2')
        self.assertIsNone(suited)

    def test_parse_suited(self):
        r1, r2, suited = parse_hand_class("AKs")
        self.assertEqual(r1, 'A')
        self.assertEqual(r2, 'K')
        self.assertTrue(suited)

        r1, r2, suited = parse_hand_class("72s")
        self.assertEqual(r1, '7')
        self.assertEqual(r2, '2')
        self.assertTrue(suited)

    def test_parse_offsuit(self):
        r1, r2, suited = parse_hand_class("AKo")
        self.assertEqual(r1, 'A')
        self.assertEqual(r2, 'K')
        self.assertFalse(suited)

        r1, r2, suited = parse_hand_class("72o")
        self.assertEqual(r1, '7')
        self.assertEqual(r2, '2')
        self.assertFalse(suited)

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            parse_hand_class("AK")   # Missing s/o

        with self.assertRaises(ValueError):
            parse_hand_class("AAo")  # Pairs can't be suited/offsuit

        with self.assertRaises(ValueError):
            parse_hand_class("XY")   # Invalid ranks

    def test_combo_counts(self):
        self.assertEqual(get_combo_count("AA"), 6)
        self.assertEqual(get_combo_count("AKs"), 4)
        self.assertEqual(get_combo_count("AKo"), 12)


class TestHandSampling(unittest.TestCase):
    def test_sample_pair(self):
        hand = sample_hand_from_class("AA")
        self.assertEqual(len(hand), 2)
        self.assertEqual(hand[0].rank, 'A')
        self.assertEqual(hand[1].rank, 'A')
        self.assertNotEqual(hand[0].suit, hand[1].suit)  # different suits

    def test_sample_suited(self):
        hand = sample_hand_from_class("AKs")
        self.assertEqual(len(hand), 2)
        self.assertEqual(hand[0].rank, 'A')
        self.assertEqual(hand[1].rank, 'K')
        self.assertEqual(hand[0].suit, hand[1].suit)     # same suit

    def test_sample_offsuit(self):
        hand = sample_hand_from_class("AKo")
        self.assertEqual(len(hand), 2)
        self.assertEqual(hand[0].rank, 'A')
        self.assertEqual(hand[1].rank, 'K')
        self.assertNotEqual(hand[0].suit, hand[1].suit)  # different suits

    def test_sample_with_exclusions(self):
        excluded = [Card('A', 's'), Card('A', 'h')]
        hand = sample_hand_from_class("AA", excluded_cards=excluded)

        # Should get remaining two aces
        self.assertEqual(len(hand), 2)
        self.assertEqual(hand[0].rank, 'A')
        self.assertEqual(hand[1].rank, 'A')
        self.assertIn(hand[0].suit, ['d', 'c'])
        self.assertIn(hand[1].suit, ['d', 'c'])


class TestEquityCalculation(unittest.TestCase):
    def test_aces_high_equity(self):
        equity = compute_heads_up_equity("AA", num_sims=50_000, seed=42)
        self.assertTrue(0.83 <= equity <= 0.87)  # ~85% +/- 2%

    def test_worst_hand_low_equity(self):
        equity = compute_heads_up_equity("72o", num_sims=50_000, seed=42)
        self.assertTrue(0.33 <= equity <= 0.37)

    def test_ak_suited_strong(self):
        equity = compute_heads_up_equity("AKs", num_sims=50_000, seed=42)
        self.assertTrue(0.64 <= equity <= 0.68)  # ~66%

    def test_medium_pairs(self):
        equity = compute_heads_up_equity("88", num_sims=30_000, seed=42)
        self.assertTrue(0.68 <= equity <= 0.72)  # ~70%

    def test_equity_reproducible_with_seed(self):
        equity1 = compute_heads_up_equity("KK", num_sims=10_000, seed=123)
        equity2 = compute_heads_up_equity("KK", num_sims=10_000, seed=123)
        self.assertEqual(equity1, equity2)

    def test_equity_converges(self):
        equity_small = compute_heads_up_equity("QQ", num_sims=1_000, seed=99)
        equity_large = compute_heads_up_equity("QQ", num_sims=50_000, seed=99)
        self.assertTrue(0.75 <= equity_small <= 0.85)
        self.assertTrue(0.78 <= equity_large <= 0.82)


class TestSpecificHandEquity(unittest.TestCase):
    def test_equity_vs_specific_hand_preflop(self):
        hero = [Card('A', 's'), Card('K', 's')]
        villain = [Card('Q', 'h'), Card('Q', 'd')]
        equity = compute_equity_vs_hand(hero, villain, num_sims=10_000, seed=42)
        self.assertTrue(0.42 <= equity <= 0.48)

    def test_equity_with_known_flop(self):
        hero = [Card('A', 's'), Card('K', 's')]
        villain = [Card('Q', 'h'), Card('Q', 'd')]
        flop = [Card('A', 'h'), Card('7', 'd'), Card('2', 'c')]

        equity = compute_equity_vs_hand(
            hero, villain, known_board=flop, num_sims=10_000, seed=42
        )
        self.assertGreater(equity, 0.80)

    def test_equity_complete_board(self):
        hero = [Card('A', 's'), Card('K', 's')]
        villain = [Card('Q', 'h'), Card('Q', 'd')]
        board = [
            Card('A', 'h'), Card('K', 'd'), Card('Q', 'c'),
            Card('7', 's'), Card('2', 'h')
        ]
        equity = compute_equity_vs_hand(hero, villain, known_board=board, num_sims=1)
        self.assertEqual(equity, 0.0)


if __name__ == '__main__':
    unittest.main()