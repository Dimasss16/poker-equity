import unittest
from src.live_odds import LiveOddsCalculator, parse_card_string, parse_cards_string
from src.deck import Card


class TestStreetProgression(unittest.TestCase):
    """Test that proper poker street progression is enforced (flop -> turn > river)."""

    def test_cannot_deal_turn_before_flop(self):
        """Cannot deal turn card before flop is dealt."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Try to deal turn without flop
        with self.assertRaisesRegex(ValueError, "Must deal flop before turn"):
            calc.deal_turn(Card('7', 'd'))

    def test_cannot_deal_river_before_turn(self):
        """Cannot deal river card before turn is dealt."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Deal flop but not turn
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])

        # Try to deal river without turn
        with self.assertRaisesRegex(ValueError, "Must deal turn before river"):
            calc.deal_river(Card('K', 'h'))

    def test_cannot_deal_river_before_flop(self):
        """Cannot deal river card before flop is dealt."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Try to deal river with no board at all
        with self.assertRaisesRegex(ValueError, "Must deal turn before river"):
            calc.deal_river(Card('K', 'h'))

    def test_cannot_deal_flop_twice(self):
        """Cannot deal flop a second time."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Deal flop once
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])

        # Try to deal flop again
        with self.assertRaisesRegex(ValueError, "Flop already dealt"):
            calc.deal_flop([Card('K', 'd'), Card('Q', 'c'), Card('J', 's')])

    def test_cannot_deal_turn_twice(self):
        """Cannot deal turn a second time."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Deal flop and turn
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        calc.deal_turn(Card('K', 'h'))

        # Try to deal turn again
        with self.assertRaisesRegex(ValueError, "Must deal flop before turn"):
            calc.deal_turn(Card('3', 'd'))

    def test_cannot_deal_river_twice(self):
        """Cannot deal river a second time."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Deal all streets
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        calc.deal_turn(Card('K', 'h'))
        calc.deal_river(Card('3', 's'))

        # Try to deal river again
        with self.assertRaisesRegex(ValueError, "Must deal turn before river"):
            calc.deal_river(Card('4', 's'))

    def test_proper_street_progression_preflop_to_river(self):
        """Test normal progression through all streets works correctly."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Should start at preflop
        self.assertEqual(calc.street, 'preflop')
        self.assertEqual(len(calc.board), 0)

        # Deal flop
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        self.assertEqual(calc.street, 'flop')
        self.assertEqual(len(calc.board), 3)

        # Deal turn
        calc.deal_turn(Card('K', 'h'))
        self.assertEqual(calc.street, 'turn')
        self.assertEqual(len(calc.board), 4)

        # Deal river
        calc.deal_river(Card('3', 's'))
        self.assertEqual(calc.street, 'river')
        self.assertEqual(len(calc.board), 5)

    def test_flop_must_be_exactly_three_cards(self):
        """Flop must be exactly 3 cards, not 1, 2, or 4."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Try 1 card
        with self.assertRaisesRegex(ValueError, "Flop must be exactly 3 cards"):
            calc.deal_flop([Card('A', 'h')])

        # Try 2 cards
        with self.assertRaisesRegex(ValueError, "Flop must be exactly 3 cards"):
            calc.deal_flop([Card('A', 'h'), Card('7', 'd')])

        # Try 4 cards
        with self.assertRaisesRegex(ValueError, "Flop must be exactly 3 cards"):
            calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c'), Card('K', 'h')])

        # Correct: 3 cards
        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        self.assertEqual(len(calc.board), 3)


class TestDuplicateCardValidation(unittest.TestCase):
    """Test that duplicate cards are properly detected and rejected."""

    def test_duplicate_within_player_hand(self):
        """Cannot add a hand with duplicate cards."""
        calc = LiveOddsCalculator(2)

        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.add_player_hand([Card('A', 's'), Card('A', 's')])

    def test_duplicate_across_player_hands(self):
        """Cannot add a second player hand that duplicates first player's cards."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])

        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.add_player_hand([Card('A', 's'), Card('Q', 'h')])

    def test_board_card_duplicates_hole_card(self):
        """Cannot deal board card that duplicates a hole card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Try to deal flop with ace of spades (already in player 1's hand)
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_flop([Card('A', 's'), Card('7', 'd'), Card('2', 'c')])

    def test_turn_card_duplicates_flop_card(self):
        """Cannot deal turn card that duplicates a flop card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])

        # Try to deal 7 of diamonds again
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_turn(Card('7', 'd'))

    def test_river_card_duplicates_turn_card(self):
        """Cannot deal river card that duplicates turn card."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        calc.deal_flop([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        calc.deal_turn(Card('K', 'h'))

        # Try to deal king of hearts again
        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.deal_river(Card('K', 'h'))

    def test_set_board_with_internal_duplicates(self):
        """Cannot set board that has duplicate cards within itself."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        with self.assertRaisesRegex(ValueError, "Duplicate card"):
            calc.set_board([
                Card('7', 'd'), Card('7', 'd'), Card('2', 'c'),
                Card('K', 'h'), Card('3', 's')
            ])


class TestFoldingValidation(unittest.TestCase):
    """Test that folding rules are properly enforced."""

    def test_cannot_fold_invalid_player_index(self):
        """Cannot fold player with invalid index."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('A', 'h')])
        calc.add_player_hand([Card('K', 'd'), Card('K', 'c')])
        calc.add_player_hand([Card('Q', 's'), Card('Q', 'h')])

        # Try to fold player 5 (doesn't exist)
        with self.assertRaisesRegex(ValueError, "Invalid player index"):
            calc.fold_player(5)

        # Try to fold player -1
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

    def test_folded_player_has_zero_equity(self):
        """Folded player receives 0% equity in calculations."""
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

    def test_last_player_standing_has_100_percent(self):
        """When only 1 player remains after folds, they have 100% equity."""
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


class TestCardParsing(unittest.TestCase):
    """Test card parsing from string input (used by API)."""

    def test_parse_valid_cards(self):
        """Parse valid card strings correctly."""
        self.assertEqual(parse_card_string("As"), Card('A', 's'))
        self.assertEqual(parse_card_string("Kh"), Card('K', 'h'))
        self.assertEqual(parse_card_string("Td"), Card('T', 'd'))
        self.assertEqual(parse_card_string("2c"), Card('2', 'c'))

    def test_parse_case_insensitive(self):
        """Card parsing should be case insensitive."""
        self.assertEqual(parse_card_string("as"), Card('A', 's'))
        self.assertEqual(parse_card_string("KH"), Card('K', 'h'))
        self.assertEqual(parse_card_string("tD"), Card('T', 'd'))

    def test_parse_invalid_card_format(self):
        """Invalid card format raises ValueError."""
        with self.assertRaises(ValueError):
            parse_card_string("XX")

        with self.assertRaises(ValueError):
            parse_card_string("A")  # too short

        with self.assertRaises(ValueError):
            parse_card_string("1s")  # invalid rank

        with self.assertRaises(ValueError):
            parse_card_string("AZ")  # invalid suit

    def test_parse_multiple_cards(self):
        """Parse space-separated card strings."""
        cards = parse_cards_string("As Kh")
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0], Card('A', 's'))
        self.assertEqual(cards[1], Card('K', 'h'))

    def test_parse_with_extra_whitespace(self):
        """Handle extra whitespace in card strings."""
        cards = parse_cards_string("  As   Qd  ")
        self.assertEqual(cards, [Card('A', 's'), Card('Q', 'd')])

    def test_parse_ten_as_T(self):
        """'10h' should be converted to 'Th' for tens."""
        card = parse_card_string("10h")
        self.assertEqual(card, Card('T', 'h'))


class TestPlayerCountValidation(unittest.TestCase):
    """Test player count validation."""

    def test_minimum_two_players(self):
        """Cannot create game with fewer than 2 players."""
        with self.assertRaises(ValueError):
            LiveOddsCalculator(1)

    def test_maximum_six_players(self):
        """Cannot create game with more than 6 players."""
        with self.assertRaises(ValueError):
            LiveOddsCalculator(7)

    def test_valid_player_counts(self):
        """Can create game with 2-6 players."""
        for num_players in range(2, 7):
            calc = LiveOddsCalculator(num_players)
            self.assertEqual(calc.num_players, num_players)

    def test_cannot_add_more_hands_than_players(self):
        """Cannot add more player hands than specified player count."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])

        with self.assertRaises(ValueError):
            calc.add_player_hand([Card('J', 'c'), Card('J', 'd')])

    def test_must_have_all_players_before_calculation(self):
        """Must add all player hands before calculating equity."""
        calc = LiveOddsCalculator(3)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('Q', 'd')])

        # Missing player 3's hand
        with self.assertRaises(ValueError):
            calc.calculate_equities(num_sims=1000)


class TestBoardSizeValidation(unittest.TestCase):
    """Test board size validation."""

    def test_board_cannot_exceed_five_cards(self):
        """Board cannot have more than 5 cards."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        with self.assertRaises(ValueError):
            calc.set_board([
                Card('A', 'h'), Card('7', 'd'), Card('2', 'c'),
                Card('K', 'h'), Card('3', 's'), Card('4', 'd')  # 6 cards
            ])

    def test_set_board_with_partial_board(self):
        """Can set board with 0-5 cards."""
        calc = LiveOddsCalculator(2)
        calc.add_player_hand([Card('A', 's'), Card('K', 's')])
        calc.add_player_hand([Card('Q', 'h'), Card('J', 'h')])

        # Empty board
        calc.set_board([])
        self.assertEqual(len(calc.board), 0)

        # Flop only
        calc.set_board([Card('A', 'h'), Card('7', 'd'), Card('2', 'c')])
        self.assertEqual(len(calc.board), 3)

        # Flop + turn
        calc.set_board([
            Card('A', 'h'), Card('7', 'd'), Card('2', 'c'),
            Card('K', 'h')
        ])
        self.assertEqual(len(calc.board), 4)

        # Complete board
        calc.set_board([
            Card('A', 'h'), Card('7', 'd'), Card('2', 'c'),
            Card('K', 'h'), Card('3', 's')
        ])
        self.assertEqual(len(calc.board), 5)


if __name__ == '__main__':
    unittest.main()