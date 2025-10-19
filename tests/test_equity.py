import unittest
from src.equity import compute_heads_up_equity, compute_equity_vs_hand, compute_multiway_equity
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
            parse_hand_class("AK")  # Missing s/o

        with self.assertRaises(ValueError):
            parse_hand_class("AAo")  # Pairs can't be suited/offsuit

        with self.assertRaises(ValueError):
            parse_hand_class("XY")  # Invalid ranks

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
        self.assertEqual(hand[0].suit, hand[1].suit)  # same suit

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


class TestHeadsUpEquity(unittest.TestCase):
    """Tests for heads-up (2-player) equity calculation."""

    def test_aces_high_equity(self):
        equity = compute_heads_up_equity("AA", num_sims=50_000, seed=42)
        self.assertTrue(0.83 <= equity <= 0.87)

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


class TestMultiwayEquity(unittest.TestCase):
    def test_aces_lower_equity_multiway(self):
        equity = compute_multiway_equity("AA", num_opponents=5, num_sims=30_000, seed=42)
        # Based on actual simulation results
        self.assertTrue(0.47 <= equity <= 0.52)  # ~49% ± 2%

    def test_worst_hand_very_low_equity_multiway(self):
        equity = compute_multiway_equity("72o", num_opponents=5, num_sims=30_000, seed=42)
        self.assertTrue(0.07 <= equity <= 0.10)

    def test_kings_multiway(self):
        equity = compute_multiway_equity("KK", num_opponents=5, num_sims=30_000, seed=42)
        self.assertTrue(0.41 <= equity <= 0.46)  # ~43% ± 2%

    def test_ak_suited_multiway(self):
        equity = compute_multiway_equity("AKs", num_opponents=5, num_sims=30_000, seed=42)
        self.assertTrue(0.29 <= equity <= 0.34)  # ~31% ± 2%

    def test_multiway_reproducible(self):
        equity1 = compute_multiway_equity("QQ", num_opponents=5, num_sims=10_000, seed=999)
        equity2 = compute_multiway_equity("QQ", num_opponents=5, num_sims=10_000, seed=999)
        self.assertEqual(equity1, equity2)

    def test_multiway_fewer_opponents(self):
        equity_headsup = compute_heads_up_equity("AA", num_sims=20_000, seed=42)
        equity_3player = compute_multiway_equity("AA", num_opponents=2, num_sims=20_000, seed=42)
        equity_6player = compute_multiway_equity("AA", num_opponents=5, num_sims=20_000, seed=42)

        # More opponents = lower equity
        self.assertGreater(equity_headsup, equity_3player)
        self.assertGreater(equity_3player, equity_6player)

    def test_trash_hand_ordering_multiway(self):
        # In 6-player, the worst hands should have very distinct equities
        equity_72o = compute_multiway_equity("72o", num_opponents=5, num_sims=20_000, seed=42)
        equity_32o = compute_multiway_equity("32o", num_opponents=5, num_sims=20_000, seed=42)
        equity_43o = compute_multiway_equity("43o", num_opponents=5, num_sims=20_000, seed=42)

        # 72o should be worst, then 32o, then 43o
        self.assertLess(equity_72o, equity_32o)
        self.assertLess(equity_32o, equity_43o)

    def test_premium_hand_ordering_multiway(self):
        equity_aa = compute_multiway_equity("AA", num_opponents=5, num_sims=20_000, seed=42)
        equity_kk = compute_multiway_equity("KK", num_opponents=5, num_sims=20_000, seed=42)
        equity_qq = compute_multiway_equity("QQ", num_opponents=5, num_sims=20_000, seed=42)

        # AA > KK > QQ
        self.assertGreater(equity_aa, equity_kk)
        self.assertGreater(equity_kk, equity_qq)


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
        # Hero has two pair (A,K); villain has a set (Q,Q,Q)
        equity = compute_equity_vs_hand(hero, villain, known_board=board, num_sims=1)
        self.assertEqual(equity, 0.0)  # Villain's set beats two pair


if __name__ == '__main__':
    unittest.main()
