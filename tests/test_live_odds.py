import unittest
from src.live_odds import (
    LiveOddsCalculator,
    parse_card_string,
    parse_cards_string,
    validate_unique_cards,
    validate_rank_count,
)
from src.deck import Card


class TestCardParsing(unittest.TestCase):
    def test_parse_single_card(self):
        self.assertEqual(parse_card_string("As"), Card('A', 's'))
        self.assertEqual(parse_card_string("Kh"), Card('K', 'h'))
        self.assertEqual(parse_card_string("Td"), Card('T', 'd'))
        self.assertEqual(parse_card_string("2c"), Card('2', 'c'))

    def test_parse_multiple_cards(self):
        cards = parse_cards_string("As Kh")
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0], Card('A', 's'))
        self.assertEqual(cards[1], Card('K', 'h'))

    def test_parse_invalid_card(self):
        with self.assertRaises(ValueError):
            parse_card_string("XX")
        with self.assertRaises(ValueError):
            parse_card_string("A")  # too short

    def test_parse_mixed_case_and_spaces(self):
        self.assertEqual(parse_card_string("tD"), Card('T', 'd'))
        self.assertEqual(parse_card_string("aS"), Card('A', 's'))
        cards = parse_cards_string("  As   Qd  ")
        self.assertEqual(cards, [Card('A', 's'), Card('Q', 'd')])

    def test_parse_invalid_rank_or_suit(self):
        with self.assertRaises(ValueError):
            parse_card_string("1s")
        with self.assertRaises(ValueError):
            parse_card_string("AZ")
        with self.assertRaises(ValueError):
            parse_card_string("Bk")  # invalid rank/suit


class TestCardValidation(unittest.TestCase):
    def test_unique_cards_valid(self):
        cards = [Card('A', 's'), Card('K', 'h'), Card('Q', 'd')]
        validate_unique_cards(cards)  # no raise

    def test_duplicate_cards_invalid(self):
        cards = [Card('A', 's'), Card('K', 'h'), Card('A', 's')]
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            validate_unique_cards(cards)

    def test_rank_count_valid(self):
        cards = [Card('A', 's'), Card('A', 'h'), Card('A', 'd'), Card('A', 'c')]
        validate_rank_count(cards)

    def test_rank_count_invalid(self):
        cards = [
            Card('A', 's'), Card('A', 'h'), Card('A', 'd'),
            Card('A', 'c'), Card('A', 's')  # duplicated to force 5 Aces
        ]
        with self.assertRaisesRegex(ValueError, r"Invalid.*rank A"):
            validate_rank_count(cards)


class TestLiveOddsCalculatorBasics(unittest.TestCase):
    def test_initialization(self):
        calc = LiveOddsCalculator(2)
        self.assertEqual(calc.num_players, 2)
        self.assertEqual(calc.player_hands, [])
        self.assertEqual(calc.board, [])
        self.assertEqual(calc.street, 'preflop')

    def test_invalid_player_count(self):
        with self.assertRaises(ValueError):
            LiveOddsCalculator(1)  # too few
        with self.assertRaises(ValueError):
            LiveOddsCalculator(7)  # too many

    def test_min_and_max_supported_players(self):
        calc2 = LiveOddsCalculator(2)
        self.assertEqual(calc2.num_players, 2)
        calc6 = LiveOddsCalculator(6)
        self.assertEqual(calc6.num_players, 6)

    def test_add_player_hands(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])
        self.assertEqual(len(calc.player_hands), 2)

    def test_add_more_hands_than_players_raises(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])
        with self.assertRaises(ValueError):
            calc.add_player_hand([Card('J', 'c'), Card('J', 'd')])

    def test_add_hand_wrong_length(self):
        calc = LiveOddsCalculator(2)
        with self.assertRaises(ValueError):
            calc.add_player_hand([Card('A', 's')])  # 1 card
        with self.assertRaises(ValueError):
            calc.add_player_hand([Card('A', 's'), Card('K', 's'), Card('Q', 's')])  # 3 cards

    def test_reject_duplicate_in_hand(self):
        calc = LiveOddsCalculator(2)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.add_player_hand([Card('A', 's'), Card('A', 's')])

    def test_reject_duplicate_across_hands(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.add_player_hand([Card('A', 's'), Card('Q', 'h')])

    def test_deal_flop_wrong_count(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])
        with self.assertRaises(ValueError):
            calc.deal_flop([Card('A', 'h'), Card('7', 'd')])  # only 2
        with self.assertRaises(ValueError):
            calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c'), Card('3', 's')])  # 4

    def test_deal_turn_wrong_street(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        with self.assertRaisesRegex(ValueError, "Must deal flop before turn"):
            calc.deal_turn(Card('7', 'd'))  # before flop

    def test_deal_river_wrong_street(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        with self.assertRaisesRegex(ValueError, "Must deal turn before river"):
            calc.deal_river(Card('K', 'h'))  # before turn

    def test_cannot_deal_flop_twice(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        with self.assertRaises(ValueError):
            calc.deal_flop([Card('K', 'd'), Card('Q', 'c'), Card('J', 's')])

    def test_cannot_deal_turn_twice(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        calc.deal_turn(Card('K', 'h'))
        with self.assertRaises(ValueError):
            calc.deal_turn(Card('3', 'd'))

    def test_cannot_deal_river_twice(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        calc.deal_turn(Card('K', 'h'))
        calc.deal_river(Card('3', 's'))
        with self.assertRaises(ValueError):
            calc.deal_river(Card('4', 's'))

    def test_reject_board_duplicate_with_hand(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('7', 'h'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'c'), Card('T', 'd')])
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('7', 'h'), Card('A', 'c'), Card('2', 'd')])

    def test_set_board_invalid_lengths(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        with self.assertRaises(ValueError):
            calc.set_board([
                Card('A', 'h'), Card('7', 'd'), Card('2', 'c'),
                Card('K', 'h'), Card('3', 's'), Card('4', 'd')  # too many
            ])

    def test_set_board_with_duplicates(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.set_board([
                Card('A', 'h'), Card('A', 'h'), Card('2', 'c'),
                Card('K', 'h'), Card('3', 's')
            ])

    def test_calculate_without_all_hands_raises(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        with self.assertRaises(ValueError):
            calc.calculate_equities(num_sims=1000, seed=1)

    def test_reproducible_with_seed(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])
        e1 = calc.calculate_equities(num_sims=2000, seed=123)
        e2 = calc.calculate_equities(num_sims=2000, seed=123)
        self.assertEqual(e1, e2)
        e3 = calc.calculate_equities(num_sims=2000, seed=124)
        self.assertTrue(any(abs(e1[i] - e3[i]) > 1e-6 for i in e1))


class TestDeterministicBoards(unittest.TestCase):

    def test_flush_vs_lower_flush(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('K', 'c'), Card('2', 'd')])
        calc.add_player_hand([Card('J', 'c'), Card('2', 'h')])
        calc.set_board([
            Card('A', 'c'), Card('9', 'c'), Card('3', 'c'),
            Card('2', 's'), Card('4', 'd')
        ])
        equities = calc.calculate_equities()
        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)

    def test_wheel_straight_beats_high_cards(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 'd'), Card('K', 'd')])
        calc.add_player_hand([Card('K', 's'), Card('Q', 'h')])
        calc.set_board([Card('5', 's'), Card('4', 'd'), Card('3', 'c'), Card('2', 'h'), Card('9', 'c')])
        equities = calc.calculate_equities()
        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)

    def test_full_house_on_board_splits(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 'h')])
        calc.add_player_hand([Card('2', 'd'), Card('3', 'c')])
        calc.set_board([Card('Q', 's'), Card('Q', 'h'), Card('Q', 'd'), Card('9', 'c'), Card('9', 'd')])
        equities = calc.calculate_equities()
        self.assertEqual(equities[0], 0.5)
        self.assertEqual(equities[1], 0.5)

    def test_set_over_set(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('K', 's'), Card('K', 'h')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])
        calc.set_board([Card('K', 'd'), Card('Q', 'd'), Card('2', 'c'), Card('7', 'h'), Card('9', 's')])
        equities = calc.calculate_equities()
        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)

    def test_split_pot_identical_hands_on_board(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('2', 's'), Card('3', 'h')])
        calc.add_player_hand([Card('4', 'd'), Card('5', 'c')])
        calc.set_board([Card('A', 's'), Card('K', 'h'), Card('Q', 'd'), Card('J', 'c'), Card('T', 's')])
        equities = calc.calculate_equities()
        self.assertEqual(equities[0], 0.5)
        self.assertEqual(equities[1], 0.5)

    def test_three_way_exact_split_on_board(self):
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('9', 's'), Card('2', 'h')])
        calc.add_player_hand([Card('8', 'd'), Card('2', 'c')])
        calc.add_player_hand([Card('7', 'h'), Card('2', 'd')])
        calc.set_board([Card('A', 's'), Card('K', 'h'), Card('Q', 'd'), Card('J', 'c'), Card('T', 's')])
        equities = calc.calculate_equities()
        self.assertAlmostEqual(equities[0], 1 / 3, places=6)
        self.assertAlmostEqual(equities[1], 1 / 3, places=6)
        self.assertAlmostEqual(equities[2], 1 / 3, places=6)


class TestMonteCarloSanity(unittest.TestCase):
    def test_preflop_aces_vs_kings(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        equities = calc.calculate_equities(num_sims=8_000, seed=42)
        self.assertTrue(0.79 <= equities[0] <= 0.85)
        self.assertTrue(0.15 <= equities[1] <= 0.21)

    def test_equities_sum_to_one_two_players(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        equities = calc.calculate_equities(num_sims=3000, seed=1)
        self.assertTrue(0.99 <= sum(equities.values()) <= 1.01)

    def test_equities_sum_to_one_four_players(self):
        calc = LiveOddsCalculator(4)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 's'), Card('K', 'h')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])
        calc.add_player_hand([Card('J', 's'), Card('J', 'h')])
        equities = calc.calculate_equities(num_sims=4000, seed=7)
        self.assertTrue(0.99 <= sum(equities.values()) <= 1.01)

    def test_seed_reproducibility_partial_board(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])
        calc.deal_flop([Card('2', 'c'), Card('7', 'd'), Card('9', 's')])
        e1 = calc.calculate_equities(num_sims=5000, seed=123)
        e2 = calc.calculate_equities(num_sims=5000, seed=123)
        self.assertEqual(e1, e2)

    def test_order_of_players_only_changes_indexing(self):
        c1 = LiveOddsCalculator(2)
        c1.add_player_hand([Card('A', 's'), Card('K', 's')])  # P0
        c1.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])  # P1
        e1 = c1.calculate_equities(num_sims=6000, seed=99)

        c2 = LiveOddsCalculator(2)
        c2.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])  # P0 (swapped)
        c2.add_player_hand([Card('A', 's'), Card('K', 's')])  # P1
        e2 = c2.calculate_equities(num_sims=6000, seed=99)

        self.assertCountEqual(list(e1.values()), list(e2.values()))


class TestStreetProgression(unittest.TestCase):
    def test_preflop_to_river(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        self.assertEqual(calc.street, 'preflop')
        self.assertEqual(len(calc.board), 0)

        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        self.assertEqual(calc.street, 'flop')
        self.assertEqual(len(calc.board), 3)

        calc.deal_turn(Card('K', 'h'))
        self.assertEqual(calc.street, 'turn')
        self.assertEqual(len(calc.board), 4)

        calc.deal_river(Card('3', 's'))
        self.assertEqual(calc.street, 'river')
        self.assertEqual(len(calc.board), 5)

    def test_cannot_skip_streets(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        with self.assertRaisesRegex(ValueError, "Must deal flop before turn"):
            calc.deal_turn(Card('7', 'd'))

        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])

        with self.assertRaisesRegex(ValueError, "Must deal turn before river"):
            calc.deal_river(Card('K', 'h'))


if __name__ == '__main__':
    unittest.main()
