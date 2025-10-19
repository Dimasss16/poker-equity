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

        # Trying to fold player 5 (doesn't exist)
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
    """Test equity calculations with folded players."""

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
    """Test folding interaction with board cards."""

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


if __name__ == '__main__':
    unittest.main()
