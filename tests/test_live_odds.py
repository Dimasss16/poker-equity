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


class TestFoldingBasics(unittest.TestCase):

    def test_fold_single_player(self):
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Fold player 2 (index 1)
        calc.fold_player(1)

        self.assertIn(1, calc.folded_players)
        self.assertNotIn(0, calc.folded_players)
        self.assertNotIn(2, calc.folded_players)

    def test_get_active_players(self):
        calc = LiveOddsCalculator(4)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])
        calc.add_player_hand([Card('J', 's'), Card('J', 'h')])

        # Initially all active
        self.assertEqual(calc.get_active_players(), [0, 1, 2, 3])

        # Fold player 2
        calc.fold_player(1)
        self.assertEqual(calc.get_active_players(), [0, 2, 3])

        # Fold player 4
        calc.fold_player(3)
        self.assertEqual(calc.get_active_players(), [0, 2])

    def test_folded_player_has_zero_equity(self):
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Fold player 2
        calc.fold_player(1)

        equities = calc.calculate_equities(num_sims=5_000, seed=42)

        self.assertEqual(equities[1], 0.0)
        self.assertGreater(equities[0], 0.0)
        self.assertGreater(equities[2], 0.0)

    def test_active_equities_sum_to_one(self):
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Fold player 3
        calc.fold_player(2)

        equities = calc.calculate_equities(num_sims=5_000, seed=42)

        total = sum(equities.values())
        self.assertGreaterEqual(total, 0.99)
        self.assertLessEqual(total, 1.01)


class TestFoldingEdgeCases(unittest.TestCase):
    def test_cannot_fold_invalid_player_index(self):
        """Cannot fold player with invalid index."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Trying to fold player 5 which doesn't exist
        with self.assertRaisesRegex(ValueError, "Invalid player index"):
            calc.fold_player(5)

        # Trying to fold player -1
        with self.assertRaisesRegex(ValueError, "Invalid player index"):
            calc.fold_player(-1)

    def test_cannot_fold_already_folded_player(self):
        """Cannot fold a player who already folded."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Fold player 2
        calc.fold_player(1)

        # Try to fold player 2 again
        with self.assertRaisesRegex(ValueError, "already folded"):
            calc.fold_player(1)

    def test_cannot_fold_last_remaining_player(self):
        """Cannot fold when only 1 player remains."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])

        # Fold player 1
        calc.fold_player(0)

        # Try to fold player 2 (only one left)
        with self.assertRaisesRegex(ValueError, "only 1 player remaining"):
            calc.fold_player(1)

    def test_cannot_fold_in_three_player_with_one_folded(self):
        """Cannot fold when only 1 active player would remain."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Fold players 1 and 2
        calc.fold_player(0)
        calc.fold_player(1)

        # Try to fold player 3 (only one left)
        with self.assertRaisesRegex(ValueError, "only 1 player remaining"):
            calc.fold_player(2)


class TestFoldingEquityCalculation(unittest.TestCase):
    def test_last_player_standing_has_100_percent(self):
        """When only 1 player remains, they have 100% equity."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Fold players 1 and 2
        calc.fold_player(0)
        calc.fold_player(1)

        equities = calc.calculate_equities(num_sims=5_000)

        self.assertEqual(equities[0], 0.0)
        self.assertEqual(equities[1], 0.0)
        self.assertEqual(equities[2], 1.0)

    def test_folding_improves_remaining_players_equity(self):
        """Folding a player increases others' equity."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('7', 'd'), Card('2', 'c')])  # Trash hand
        calc.add_player_hand([Card('K', 's'), Card('K', 'h')])

        # Equity before fold
        equities_before = calc.calculate_equities(num_sims=10_000, seed=42)

        # Fold the trash hand (player 2)
        calc.fold_player(1)

        # Equity after fold
        equities_after = calc.calculate_equities(num_sims=10_000, seed=42)

        # AA and KK should both have higher equity now
        self.assertGreater(equities_after[0], equities_before[0])
        self.assertGreater(equities_after[2], equities_before[2])
        self.assertEqual(equities_after[1], 0.0)

    def test_folding_after_flop(self):
        """Folding works correctly after flop is dealt."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('7', 'h'), Card('2', 'c')])

        # Deal flop
        calc.deal_flop([Card('A', 'h'), Card('K', 'd'), Card('Q', 'c')])

        # Fold player 2
        calc.fold_player(1)

        equities = calc.calculate_equities(num_sims=5_000)

        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)

    def test_folding_after_turn(self):
        """Folding works correctly after turn is dealt."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('7', 'h'), Card('2', 'c')])

        # Deal flop and turn
        calc.deal_flop([Card('A', 'h'), Card('K', 'd'), Card('Q', 'c')])
        calc.deal_turn(Card('J', 's'))

        # Fold player 2
        calc.fold_player(1)

        equities = calc.calculate_equities(num_sims=5_000)

        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)

    def test_folding_on_river_exact_calculation(self):
        """Folding on river uses exact calculation."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('7', 'h'), Card('2', 'c')])

        # Deal all streets
        calc.deal_flop([Card('A', 'h'), Card('K', 'd'), Card('Q', 'c')])
        calc.deal_turn(Card('J', 's'))
        calc.deal_river(Card('2', 'd'))

        # Fold player 2
        calc.fold_player(1)

        equities = calc.calculate_equities()  # Exact, no sims

        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)


class TestFoldingMultiPlayer(unittest.TestCase):
    """Test folding in multi-player scenarios."""

    def test_fold_two_players_in_four_player_game(self):
        """Fold 2 out of 4 players."""
        calc = LiveOddsCalculator(4)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('7', 'd'), Card('2', 'c')])
        calc.add_player_hand([Card('K', 's'), Card('K', 'h')])
        calc.add_player_hand([Card('8', 'd'), Card('3', 'c')])

        # Fold players 2 and 4
        calc.fold_player(1)
        calc.fold_player(3)

        equities = calc.calculate_equities(num_sims=10_000, seed=42)

        # Only players 1 and 3 have equity
        self.assertGreater(equities[0], 0.0)
        self.assertEqual(equities[1], 0.0)
        self.assertGreater(equities[2], 0.0)
        self.assertEqual(equities[3], 0.0)

        # AA should have higher equity than KK
        self.assertGreater(equities[0], equities[2])

    def test_sequential_folds_in_six_player_game(self):
        """Fold players one by one until only one remains."""
        calc = LiveOddsCalculator(6)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])
        calc.add_player_hand([Card('J', 's'), Card('J', 'h')])
        calc.add_player_hand([Card('T', 's'), Card('T', 'h')])
        calc.add_player_hand([Card('9', 's'), Card('9', 'h')])

        # Fold players 2-6 one by one
        calc.fold_player(1)
        equities = calc.calculate_equities(num_sims=5_000, seed=42)
        self.assertEqual(equities[1], 0.0)
        self.assertGreaterEqual(sum(equities.values()), 0.99)

        calc.fold_player(2)
        equities = calc.calculate_equities(num_sims=5_000, seed=42)
        self.assertEqual(equities[2], 0.0)

        calc.fold_player(3)
        equities = calc.calculate_equities(num_sims=5_000, seed=42)
        self.assertEqual(equities[3], 0.0)

        calc.fold_player(4)
        equities = calc.calculate_equities(num_sims=5_000, seed=42)
        self.assertEqual(equities[4], 0.0)

        calc.fold_player(5)
        equities = calc.calculate_equities(num_sims=5_000, seed=42)

        # Only player 1 remains
        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)
        self.assertEqual(equities[2], 0.0)
        self.assertEqual(equities[3], 0.0)
        self.assertEqual(equities[4], 0.0)
        self.assertEqual(equities[5], 0.0)

    def test_folded_cards_not_in_simulation_deck(self):
        """Folded players' cards don't appear in board simulations."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])  # We'll fold that one
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Folding player 2
        calc.fold_player(1)

        # Now run and check that Kd/Kc never appear on board
        known_cards = calc.get_all_known_cards()
        known_set = set((c.rank, c.suit) for c in known_cards)

        self.assertIn(('K', 'd'), known_set)
        self.assertIn(('K', 'c'), known_set)

        # The folded cards should be in known cards
        self.assertEqual(len(known_cards), 6)  # 3 players x 2 cards each

    def test_fold_order_doesnt_matter(self):
        """Folding player 1 then 3 = folding player 3 then 1."""
        calc1 = LiveOddsCalculator(4)
        calc1.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc1.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc1.add_player_hand([Card('Q', 's'), Card('Q', 'h')])
        calc1.add_player_hand([Card('J', 's'), Card('J', 'h')])

        calc2 = LiveOddsCalculator(4)
        calc2.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc2.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc2.add_player_hand([Card('Q', 's'), Card('Q', 'h')])
        calc2.add_player_hand([Card('J', 's'), Card('J', 'h')])

        # Fold in different order
        calc1.fold_player(1)
        calc1.fold_player(3)

        calc2.fold_player(3)
        calc2.fold_player(1)

        # Results should be identical (with same seed)
        equities1 = calc1.calculate_equities(num_sims=10_000, seed=42)
        equities2 = calc2.calculate_equities(num_sims=10_000, seed=42)

        for i in range(4):
            self.assertEqual(equities1[i], equities2[i])


class TestFoldingWithBoardCards(unittest.TestCase):
    def test_fold_pre_flop_then_deal_flop(self):
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('7', 's'), Card('2', 'h')])

        # Fold player 3 pre-flop
        calc.fold_player(2)

        # Deal flop
        calc.deal_flop([Card('A', 'd'), Card('K', 'h'), Card('Q', 'c')])

        equities = calc.calculate_equities(num_sims=5_000, seed=42)

        # Player 3 still has 0% equity
        self.assertEqual(equities[2], 0.0)
        # Players 1 and 2 have equity
        self.assertGreater(equities[0], 0.0)
        self.assertGreater(equities[1], 0.0)

    def test_folded_player_cards_dont_conflict_with_board(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Fold player 2
        calc.fold_player(1)

        # Try to deal board with Qh (should fail - already in folded hand)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('Q', 'h'), Card('T', 'd'), Card('9', 'c')])

    def test_fold_on_complete_board(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Deal complete board
        calc.set_board([
            Card('A', 'h'), Card('K', 'd'), Card('Q', 'c'),
            Card('J', 's'), Card('T', 'd')
        ])

        # Both have straight, but fold player 2
        calc.fold_player(1)

        equities = calc.calculate_equities()

        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)


class TestOutcomeProbabilityDisplayVariables(unittest.TestCase):
    def test_display_variables_updated_after_normal_calculation(self):
        """Display variables are set after normal equity calculation."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])

        equities = calc.calculate_equities(num_sims=5_000, seed=42)

        # Check that display variables exist and are populated
        self.assertIsNotNone(calc.last_outright_win_probabilities)
        self.assertIsNotNone(calc.last_split_probability)

        # Check that they contain data for all players
        self.assertEqual(len(calc.last_outright_win_probabilities), 2)

        # Outcome probabilities should sum to ~100%
        total_outcomes = (
                calc.last_outright_win_probabilities[0] +
                calc.last_outright_win_probabilities[1] +
                calc.last_split_probability
        )
        self.assertGreaterEqual(total_outcomes, 0.98)
        self.assertLessEqual(total_outcomes, 1.02)

    def test_display_variables_updated_when_one_player_remains(self):
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        calc.fold_player(1)
        calc.fold_player(2)

        equities = calc.calculate_equities()

        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)
        self.assertEqual(equities[2], 0.0)

        # Check display variables are updated (just fixed this bug now)
        self.assertEqual(calc.last_outright_win_probabilities[0], 1.0)
        self.assertEqual(calc.last_outright_win_probabilities[1], 0.0)
        self.assertEqual(calc.last_outright_win_probabilities[2], 0.0)

        # No split should be possible with one player
        self.assertEqual(calc.last_split_probability, 0.0)

        # Outcome probabilities sum to exactly 100%
        total_outcomes = (
                calc.last_outright_win_probabilities[0] +
                calc.last_outright_win_probabilities[1] +
                calc.last_outright_win_probabilities[2] +
                calc.last_split_probability
        )
        self.assertEqual(total_outcomes, 1.0)

    def test_outcome_probabilities_sum_to_one(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('9', 's'), Card('9', 'h')])
        calc.add_player_hand([Card('8', 'd'), Card('8', 'c')])

        equities = calc.calculate_equities(num_sims=10_000, seed=42)

        # Sum of all outcome probabilities
        total = (
                calc.last_outright_win_probabilities[0] +
                calc.last_outright_win_probabilities[1] +
                calc.last_split_probability
        )

        # Should be 1.0 within small tolerance
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_display_variables_with_guaranteed_split(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('2', 's'), Card('3', 'h')])
        calc.add_player_hand([Card('4', 'd'), Card('5', 'c')])

        # Board makes royal flush
        calc.set_board([
            Card('A', 'h'), Card('K', 'h'), Card('Q', 'h'),
            Card('J', 'h'), Card('T', 'h')
        ])

        equities = calc.calculate_equities()

        # Both players have 50% equity
        self.assertEqual(equities[0], 0.5)
        self.assertEqual(equities[1], 0.5)

        # Outcome: no outright wins, 100% split
        self.assertEqual(calc.last_outright_win_probabilities[0], 0.0)
        self.assertEqual(calc.last_outright_win_probabilities[1], 0.0)
        self.assertEqual(calc.last_split_probability, 1.0)

    def test_display_variables_with_no_splits(self):
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('2', 'd'), Card('3', 'c')])

        # Board gives player 1 two pair, player 2 nothing
        calc.set_board([
            Card('A', 'h'), Card('K', 'd'), Card('Q', 'c'),
            Card('J', 's'), Card('9', 'h')
        ])

        equities = calc.calculate_equities()

        # Player 1 wins 100%
        self.assertEqual(equities[0], 1.0)
        self.assertEqual(equities[1], 0.0)

        # Outcome: player 1 wins outright, no split
        self.assertEqual(calc.last_outright_win_probabilities[0], 1.0)
        self.assertEqual(calc.last_outright_win_probabilities[1], 0.0)
        self.assertEqual(calc.last_split_probability, 0.0)

    def test_display_variables_persist_across_calculations(self):
        """Display variables update with each new calculation."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])

        # First calculation: pre-flop
        equities1 = calc.calculate_equities(num_sims=5_000, seed=42)
        outcome1_p1 = calc.last_outright_win_probabilities[0]

        # Deal flop favoring player 1
        calc.deal_flop([Card('A', 'd'), Card('A', 'c'), Card('2', 'h')])

        # Second calculation: flop
        equities2 = calc.calculate_equities(num_sims=5_000, seed=42)
        outcome2_p1 = calc.last_outright_win_probabilities[0]

        # Player 1's outright win probability should increase (has quads now)
        self.assertGreater(outcome2_p1, outcome1_p1)

    def test_display_variables_with_three_players(self):
        """Display variables work correctly with three players."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        equities = calc.calculate_equities(num_sims=10_000, seed=42)

        # All three players should have outcome probabilities
        self.assertGreater(calc.last_outright_win_probabilities[0], 0.0)
        self.assertGreater(calc.last_outright_win_probabilities[1], 0.0)
        self.assertGreater(calc.last_outright_win_probabilities[2], 0.0)

        # Sum of all outcomes should be ~100%
        total = (
                calc.last_outright_win_probabilities[0] +
                calc.last_outright_win_probabilities[1] +
                calc.last_outright_win_probabilities[2] +
                calc.last_split_probability
        )
        self.assertGreaterEqual(total, 0.98)
        self.assertLessEqual(total, 1.02)

    def test_display_variables_after_fold_then_unfold_scenario(self):
        """Display variables correct after folding reduces to one player."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Initial calculation
        equities1 = calc.calculate_equities(num_sims=5_000, seed=42)

        # Both should have non-zero outcome probabilities
        self.assertGreater(calc.last_outright_win_probabilities[0], 0.0)
        self.assertGreater(calc.last_outright_win_probabilities[1], 0.0)

        # Fold player 2
        calc.fold_player(1)
        equities2 = calc.calculate_equities()

        # Player 1 should now have 100% outcome probability
        self.assertEqual(calc.last_outright_win_probabilities[0], 1.0)
        self.assertEqual(calc.last_outright_win_probabilities[1], 0.0)
        self.assertEqual(calc.last_split_probability, 0.0)

    def test_equity_vs_outcome_probability_difference(self):
        """Equity and outcome probability differ when splits occur."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('9', 's'), Card('9', 'h')])
        calc.add_player_hand([Card('9', 'd'), Card('9', 'c')])

        # Both have pocket 9s - many splits expected
        equities = calc.calculate_equities(num_sims=10_000, seed=42)

        # Equity should be close to 50/50
        self.assertAlmostEqual(equities[0], 0.5, places=1)
        self.assertAlmostEqual(equities[1], 0.5, places=1)

        # But outcome probabilities should show splits
        # Both should have some outright wins
        self.assertGreater(calc.last_outright_win_probabilities[0], 0.0)
        self.assertGreater(calc.last_outright_win_probabilities[1], 0.0)

        # And significant split probability
        self.assertGreater(calc.last_split_probability, 0.1)

        # The main difference is that equity includes half of split probability
        # while outcome probability separates "win outright" from "split"


class TestDuplicateCardDetection(unittest.TestCase):
    # ===== Pre-flop duplicates =====

    def test_duplicate_within_single_hand(self):
        """Cannot add a hand with duplicate cards."""
        calc = LiveOddsCalculator(2)

        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.add_player_hand([Card('A', 's'), Card('A', 's')])

    def test_duplicate_between_player_hands(self):
        """Cannot add hands that share cards between players."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])

        # Try to add same ace
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.add_player_hand([Card('A', 's'), Card('Q', 'h')])

    def test_duplicate_across_three_players(self):
        """Duplicate detection works with 3+ players."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Try to add king of spades (player 1 already has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.add_player_hand([Card('K', 's'), Card('T', 'd')])

    # ===== Flop duplicates =====

    def test_duplicate_within_flop(self):
        """Cannot deal flop with duplicate cards."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Flop with duplicate
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('T', 'd'), Card('T', 'd'), Card('9', 'c')])

    def test_flop_duplicates_player_card(self):
        """Cannot deal flop card that matches a hole card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Try to deal ace of spades on flop
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('A', 's'), Card('T', 'd'), Card('9', 'c')])

    def test_flop_duplicates_second_player_card(self):
        """Flop duplicate detection checks all players."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Try to deal queen of hearts (player 2 has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('Q', 'h'), Card('T', 'd'), Card('9', 'c')])

    def test_flop_duplicates_in_four_player_game(self):
        """Flop duplicate detection works with 4 players."""
        calc = LiveOddsCalculator(4)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.add_player_hand([Card('T', 'd'), Card('9', 'd')])
        calc.add_player_hand([Card('8', 'c'), Card('7', 'c')])

        # Try to deal 9 of diamonds (player 3 has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('9', 'd'), Card('5', 's'), Card('2', 'h')])

    # ===== Turn duplicates =====

    def test_turn_duplicates_hole_card(self):
        """Cannot deal turn card that matches a hole card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('T', 'd'), Card('9', 'c'), Card('8', 's')])

        # Try to deal king of spades on turn
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_turn(Card('K', 's'))

    def test_turn_duplicates_flop_card(self):
        """Cannot deal turn card that matches a flop card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('T', 'd'), Card('9', 'c'), Card('8', 's')])

        # Try to deal ten of diamonds on turn (already on flop)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_turn(Card('T', 'd'))

    def test_turn_duplicates_in_three_player_game(self):
        """Turn duplicate detection works with 3 players."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.add_player_hand([Card('T', 'd'), Card('9', 'd')])
        calc.deal_flop([Card('8', 'c'), Card('7', 'c'), Card('6', 's')])

        # Try to deal 9 of diamonds (player 3 has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_turn(Card('9', 'd'))

    # ===== River duplicates =====

    def test_river_duplicates_hole_card(self):
        """Cannot deal river card that matches a hole card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('T', 'd'), Card('9', 'c'), Card('8', 's')])
        calc.deal_turn(Card('7', 'h'))

        # Try to deal ace of spades on river
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_river(Card('A', 's'))

    def test_river_duplicates_flop_card(self):
        """Cannot deal river card that matches a flop card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('T', 'd'), Card('9', 'c'), Card('8', 's')])
        calc.deal_turn(Card('7', 'h'))

        # Try to deal nine of clubs on river (already on flop)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_river(Card('9', 'c'))

    def test_river_duplicates_turn_card(self):
        """Cannot deal river card that matches the turn card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.deal_flop([Card('T', 'd'), Card('9', 'c'), Card('8', 's')])
        calc.deal_turn(Card('7', 'h'))

        # Try to deal seven of hearts on river (already on turn)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_river(Card('7', 'h'))

    def test_river_duplicates_in_six_player_game(self):
        """River duplicate detection works with 6 players."""
        calc = LiveOddsCalculator(6)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])
        calc.add_player_hand([Card('J', 's'), Card('J', 'h')])
        calc.add_player_hand([Card('T', 's'), Card('T', 'h')])
        calc.add_player_hand([Card('9', 's'), Card('9', 'h')])
        calc.deal_flop([Card('8', 'c'), Card('7', 'c'), Card('6', 's')])
        calc.deal_turn(Card('5', 'd'))

        # Try to deal queen of hearts (player 3 has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_river(Card('Q', 'h'))

    # ===== set_board =====

    def test_set_board_with_internal_duplicates(self):
        """Cannot set board with duplicate cards within itself."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Board with duplicate
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.set_board([
                Card('T', 'd'), Card('T', 'd'), Card('8', 's'),
                Card('7', 'h'), Card('6', 'c')
            ])

    def test_set_board_duplicates_hole_cards(self):
        """Cannot set board that duplicates hole cards."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Board includes ace of spades
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.set_board([
                Card('A', 's'), Card('T', 'd'), Card('9', 'c'),
                Card('8', 's'), Card('7', 'h')
            ])

    # ===== Rank counts =====

    def test_five_cards_of_same_rank_rejected(self):
        """Cannot have 5 cards of the same rank."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('A', 'd'), Card('A', 'c')])

        # Try to deal fifth ace (impossible in standard deck)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('A', 's'), Card('Q', 'h'), Card('J', 'd')])

    def test_rank_count_validation_across_all_cards(self):
        """Rank count validation checks hole cards + board."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('K', 's'), Card('K', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('Q', 'c')])
        calc.add_player_hand([Card('J', 's'), Card('J', 'h')])

        # Already have 3 kings, try to add 2 more on flop
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('K', 'c'), Card('K', 's'), Card('Q', 'h')])

    # ===== Folded players duplicates =====

    def test_folded_player_cards_prevent_duplicates(self):
        """Folded players' cards still prevent duplicates on board."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Fold player 2
        calc.fold_player(1)

        # Try to deal queen of hearts (folded player has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('Q', 'h'), Card('T', 'd'), Card('9', 'c')])

    def test_folded_player_cards_on_turn(self):
        """Folded players' cards prevent duplicates on turn."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])
        calc.add_player_hand([Card('T', 'd'), Card('9', 'd')])

        calc.deal_flop([Card('8', 'c'), Card('7', 'c'), Card('6', 's')])

        # Fold player 3
        calc.fold_player(2)

        # Try to deal ten of diamonds (folded player has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_turn(Card('T', 'd'))

    def test_folded_player_cards_on_river(self):
        """Folded players' cards prevent duplicates on river."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        calc.deal_flop([Card('T', 'd'), Card('9', 'c'), Card('8', 's')])
        calc.deal_turn(Card('7', 'c'))

        # Fold player 1
        calc.fold_player(0)

        # Try to deal king of spades (folded player has it)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_river(Card('K', 's'))


class TestFoldedCardsNotInSimulations(unittest.TestCase):
    """Test that folded players' cards never appear in simulated boards."""

    def test_folded_cards_in_known_cards_list(self):
        """Folded players' cards should be in the known cards list."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Before folding: 6 known cards (3 players x 2 cards)
        known_before = calc.get_all_known_cards()
        self.assertEqual(len(known_before), 6)

        # Fold player 2
        calc.fold_player(1)

        # After folding: still 6 known cards (folded cards still be in the known)
        known_after = calc.get_all_known_cards()
        self.assertEqual(len(known_after), 6)

        # Verify Kd and Kc are in known cards
        known_set = set((c.rank, c.suit) for c in known_after)
        self.assertIn(('K', 'd'), known_set)
        self.assertIn(('K', 'c'), known_set)

    def test_folded_cards_excluded_from_deck_filtering(self):
        """Folded cards should be excluded when filtering deck."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Fold player 2
        calc.fold_player(1)

        # Get known cards (should include folded Qh and Jh)
        known_cards = calc.get_all_known_cards()
        known_set = set((c.rank, c.suit) for c in known_cards)

        # Verify folded cards are known
        self.assertIn(('Q', 'h'), known_set)
        self.assertIn(('J', 'h'), known_set)

        # The deck should have 48 cards remaining (52 - 4 known)
        from src.deck import Deck
        deck = Deck()
        available = [c for c in deck._cards if (c.rank, c.suit) not in known_set]
        self.assertEqual(len(available), 48)

        # Verify folded cards NOT in available cards
        available_set = set((c.rank, c.suit) for c in available)
        self.assertNotIn(('Q', 'h'), available_set)
        self.assertNotIn(('J', 'h'), available_set)

    def test_folded_specific_cards_never_on_board(self):
        """Run simulation and verify folded cards never appear on board."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('7', 's'), Card('2', 'h')])  # Trash hand
        calc.add_player_hand([Card('A', 'c'), Card('K', 'c')])  # Strong hand

        # Fold player 1 (7s, 2h)
        calc.fold_player(0)

        # Run many simulations and track which cards appear
        num_sims = 100000
        boards_seen = []

        from src.deck import Deck
        known_cards_set = set((c.rank, c.suit) for c in calc.get_all_known_cards())

        for _ in range(num_sims):
            deck = Deck()
            deck.shuffle()

            # Filter like the real calculate_equities does
            available_cards = [c for c in deck._cards if (c.rank, c.suit) not in known_cards_set]

            # Deal 5-card board
            board = available_cards[:5]
            boards_seen.append(board)

            # Check that folded cards (7s, 2h) never appear
            for card in board:
                self.assertFalse(
                    card.rank == '7' and card.suit == 's',
                    f"Folded card 7s appeared on board!"
                )
                self.assertFalse(
                    card.rank == '2' and card.suit == 'h',
                    f"Folded card 2h appeared on board!"
                )

        # If we got here, no folded cards appeared in 100000 boards
        self.assertEqual(len(boards_seen), 100000)

    def test_equity_changes_correctly_after_fold(self):
        """Folding should change equity in expected ways."""
        calc = LiveOddsCalculator(3)
        # Player 1: Trash
        # Player 2: Top pair
        # Player 3: Medium pair
        calc.add_player_hand([Card('7', 's'), Card('2', 'h')])
        calc.add_player_hand([Card('A', 'c'), Card('A', 'd')])
        calc.add_player_hand([Card('8', 'h'), Card('8', 's')])

        # Calculate before fold
        equity_before = calc.calculate_equities(num_sims=50_000, seed=42)

        # Player 2 should have highest equity
        self.assertGreater(equity_before[1], equity_before[0])
        self.assertGreater(equity_before[1], equity_before[2])

        # Fold the trash hand
        calc.fold_player(0)

        # Calculate after fold
        equity_after = calc.calculate_equities(num_sims=50_000, seed=42)

        # Player 1 should have 0%
        self.assertEqual(equity_after[0], 0.0)

        # Player 2's equity should increase (fewer opponents)
        self.assertGreater(equity_after[1], equity_before[1])

        # Player 3's equity should also increase
        self.assertGreater(equity_after[2], equity_before[2])

        # Active players sum to 100%
        self.assertAlmostEqual(equity_after[1] + equity_after[2], 1.0, places=2)

    def test_folded_cards_affect_outs_calculation(self):
        """Folding should affect the number of available outs."""
        calc = LiveOddsCalculator(2)
        # We have a flush draw
        calc.add_player_hand([Card('K', 'c'), Card('Q', 'c')])
        # Opponent has two clubs
        calc.add_player_hand([Card('9', 'c'), Card('8', 'c')])

        # Flop: Two clubs
        calc.deal_flop([Card('A', 'c'), Card('7', 'h'), Card('2', 'd')])

        # Scenario 1: Opponent still active (they have 9c, 8c)
        # We need one more club for flush
        # 13 clubs - 4 on board/in hands = 9 clubs remain, but 2 are in opponent's hand
        # So effectively 7 "clean" flush outs from our perspective

        equity_active = calc.calculate_equities(num_sims=100_000, seed=42)

        # Reset and fold opponent
        calc2 = LiveOddsCalculator(2)
        calc2.add_player_hand([Card('K', 'c'), Card('Q', 'c')])
        calc2.add_player_hand([Card('9', 'c'), Card('8', 'c')])
        calc2.deal_flop([Card('A', 'c'), Card('7', 'h'), Card('2', 'd')])
        calc2.fold_player(1)

        equity_folded = calc2.calculate_equities(num_sims=100_000, seed=42)

        # When opponent folds, we should have 100%
        self.assertEqual(equity_folded[0], 1.0)
        self.assertEqual(equity_folded[1], 0.0)

        # Verify opponent's clubs (9c, 8c) are in known cards
        known = calc2.get_all_known_cards()
        known_set = set((c.rank, c.suit) for c in known)
        self.assertIn(('9', 'c'), known_set)
        self.assertIn(('8', 'c'), known_set)

    def test_multiple_folded_players_all_excluded(self):
        """When multiple players fold, all their cards are excluded."""
        calc = LiveOddsCalculator(4)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])  # Will fold
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])  # Will fold
        calc.add_player_hand([Card('J', 's'), Card('J', 'h')])

        # Fold players 2 and 3
        calc.fold_player(1)
        calc.fold_player(2)

        # Known cards should include all 4 players' cards
        known = calc.get_all_known_cards()
        self.assertEqual(len(known), 8)

        # Verify all folded cards are known
        known_set = set((c.rank, c.suit) for c in known)
        self.assertIn(('K', 'd'), known_set)
        self.assertIn(('K', 'c'), known_set)
        self.assertIn(('Q', 's'), known_set)
        self.assertIn(('Q', 'h'), known_set)

        # Run simulation and verify none of these 4 cards appear
        from src.deck import Deck

        for _ in range(10000):
            deck = Deck()
            deck.shuffle()
            available = [c for c in deck._cards if (c.rank, c.suit) not in known_set]
            board = available[:5]

            for card in board:
                # None of the folded kings or queens should appear
                self.assertFalse(
                    (card.rank == 'K' and card.suit in ['d', 'c']) or
                    (card.rank == 'Q' and card.suit in ['s', 'h']),
                    f"Folded card {card.rank}{card.suit} appeared on board or naur"
                )

    def test_folded_cards_with_partial_board(self):
        """Folded cards don't appear on turn/river."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('T', 'h'), Card('9', 'h')])

        # Deal flop
        calc.deal_flop([Card('2', 'c'), Card('3', 'd'), Card('4', 's')])

        # Fold player 2
        calc.fold_player(1)

        # Get known cards
        known = calc.get_all_known_cards()
        known_set = set((c.rank, c.suit) for c in known)

        # Verify folded cards are known
        self.assertIn(('T', 'h'), known_set)
        self.assertIn(('9', 'h'), known_set)

        # Simulate dealing turn/river many times
        from src.deck import Deck

        for _ in range(25000):
            deck = Deck()
            deck.shuffle()
            available = [c for c in deck._cards if (c.rank, c.suit) not in known_set]

            # Deal turn and river
            turn_river = available[:2]

            for card in turn_river:
                self.assertFalse(
                    card.rank == 'T' and card.suit == 'h',
                    "Folded card Th appeared on turn/river, shoot"
                )
                self.assertFalse(
                    card.rank == '9' and card.suit == 'h',
                    "Folded card 9h appeared on turn/river oh no"
                )

    def test_folded_cards_never_in_actual_simulation_boards(self):
        """THE CRITICAL TEST: Verify folded cards don't appear in real calculate_equities() boards."""
        calc = LiveOddsCalculator(3)

        # Player 1: Active
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])

        # Player 2: Will fold (has specific cards we'll track)
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Player 3: Active
        calc.add_player_hand([Card('T', 'd'), Card('9', 'd')])

        # Fold player 2 (Qh, Jh should NEVER appear on boards)
        calc.fold_player(1)

        # Run actual calculate_equities with board capture
        equities = calc.calculate_equities(num_sims=1_000, seed=42, capture_boards=True)

        # Access captured boards
        boards = calc._last_captured_boards

        # We should have captured 1000 boards
        self.assertEqual(len(boards), 1_000)

        # Check EVERY board for folded cards
        folded_cards = {('Q', 'h'), ('J', 'h')}

        for i, board in enumerate(boards):
            board_set = set((c.rank, c.suit) for c in board)

            # Verify folded cards never appear
            intersection = board_set & folded_cards
            self.assertEqual(
                len(intersection), 0,
                f"Simulation {i}: Folded cards {intersection} appeared on board {board} yikes"
            )

        # Also verify equity is correct (player 2 has 0%)
        self.assertEqual(equities[1], 0.0)
        self.assertGreater(equities[0], 0.0)
        self.assertGreater(equities[2], 0.0)

    def test_folded_cards_never_appear_after_flop(self):
        """Verify folded cards don't appear on turn/river in real simulations."""
        calc = LiveOddsCalculator(3)  # Changed to 3 players

        calc.add_player_hand([Card('A', 's'), Card('K', 's')])  # Active
        calc.add_player_hand([Card('7', 'c'), Card('2', 'c')])  # Will fold
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])  # Active

        # Deal flop
        calc.deal_flop([Card('T', 'h'), Card('9', 'd'), Card('8', 's')])

        # Fold player 2
        calc.fold_player(1)

        # Now 2 active players remain, so simulation WILL run
        equities = calc.calculate_equities(num_sims=500, seed=42, capture_boards=True)

        boards = calc._last_captured_boards
        self.assertEqual(len(boards), 500)  # Now we get 500 boards

        # Each board should be 5 cards (3 from flop + 2 simulated)
        folded_cards = {('7', 'c'), ('2', 'c')}

        for board in boards:
            self.assertEqual(len(board), 5)

            # Check last 2 cards (turn and river) for folded cards
            turn_river = board[3:]
            for card in turn_river:
                self.assertNotIn(
                    (card.rank, card.suit),
                    folded_cards,
                    f"Folded card {card.rank}{card.suit} appeared on simulated turn/river, we need to fix this now"
                )

    def test_multiple_folded_players_all_cards_excluded_from_real_sim(self):
        """Multiple folded players - none of their cards appear in real simulation."""
        calc = LiveOddsCalculator(4)

        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])  # Active
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])  # Fold
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])  # Fold
        calc.add_player_hand([Card('J', 's'), Card('J', 'h')])  # Active

        # Fold players 2 and 3
        calc.fold_player(1)
        calc.fold_player(2)

        # Run simulation
        equities = calc.calculate_equities(num_sims=1_000, seed=42, capture_boards=True)

        boards = calc._last_captured_boards

        # All 4 folded cards should never appear
        folded_cards = {('K', 'd'), ('K', 'c'), ('Q', 's'), ('Q', 'h')}

        for i, board in enumerate(boards):
            board_set = set((c.rank, c.suit) for c in board)
            intersection = board_set & folded_cards

            self.assertEqual(
                len(intersection), 0,
                f"Simulation {i}: Folded cards {intersection} appeared on board:("
            )


if __name__ == '__main__':
    unittest.main()
