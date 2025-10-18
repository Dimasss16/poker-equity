from typing import List, Dict
import random
from src.deck import Deck, Card
from src.evaluator import evaluate


def validate_unique_cards(all_cards: List[Card]):
    seen = set()
    for card in all_cards:
        card_id = (card.rank, card.suit)
        if card_id in seen:
            raise ValueError(f"Duplicate card: {card.rank}{card.suit}")
        seen.add(card_id)


def validate_rank_count(all_cards: List[Card]):
    from collections import Counter
    rank_counts = Counter(card.rank for card in all_cards)

    for rank, count in rank_counts.items():
        if count > 4:
            raise ValueError(f"Invalid: {count} cards of rank {rank} (max 4 allowed)")


class LiveOddsCalculator:
    """
    Calculate live equity for multiple players with known hole cards.

    Supports 2-6 players and updates equity as board cards are revealed.
    """

    def __init__(self, num_players: int):
        if not 2 <= num_players <= 6:
            raise ValueError("Number of players must be between 2 and 6")

        self.num_players = num_players
        self.player_hands: List[List[Card]] = []
        self.board: List[Card] = []
        self.street = 'preflop'

    def add_player_hand(self, hand: List[Card]):
        if len(hand) != 2:
            raise ValueError("Each player must have exactly 2 hole cards")

        if len(self.player_hands) >= self.num_players:
            raise ValueError(f"Already have {self.num_players} players")

        # Validate no duplicates within this hand
        validate_unique_cards(hand)

        # Validate no conflicts with already-added hands
        all_known = self.get_all_known_cards()
        validate_unique_cards(all_known + hand)

        # Validate rank counts
        validate_rank_count(all_known + hand)

        self.player_hands.append(hand)

    def set_board(self, cards: List[Card]):
        """
        Set the board cards (replaces existing board).

        Args:
            cards: 0-5 community cards

        Raises:
            ValueError: If invalid board size, duplicate cards, or conflicts with hole cards
        """
        if len(cards) > 5:
            raise ValueError("Board cannot have more than 5 cards")

        # Validate no duplicates within board
        validate_unique_cards(cards)

        # Validate no conflicts with player hands
        all_known = self.get_all_known_cards()
        all_with_new_board = []
        for hand in self.player_hands:
            all_with_new_board.extend(hand)
        all_with_new_board.extend(cards)

        validate_unique_cards(all_with_new_board)
        validate_rank_count(all_with_new_board)

        self.board = cards

        # Update street name
        if len(cards) == 0:
            self.street = 'preflop'
        elif len(cards) == 3:
            self.street = 'flop'
        elif len(cards) == 4:
            self.street = 'turn'
        elif len(cards) == 5:
            self.street = 'river'

    def deal_flop(self, cards: List[Card]):
        if self.street != 'preflop' or len(self.board) != 0:
            raise ValueError("Flop already dealt")
        if len(cards) != 3:
            raise ValueError("Flop must be exactly 3 cards")
        self.set_board(cards)

    def deal_turn(self, card: Card):
        if len(self.board) != 3:
            raise ValueError("Must deal flop before turn")

        # Validate card doesn't conflict
        all_known = self.get_all_known_cards()
        validate_unique_cards(all_known + [card])
        validate_rank_count(all_known + [card])

        self.board.append(card)
        self.street = 'turn'

    def deal_river(self, card: Card):
        if len(self.board) != 4:
            raise ValueError("Must deal turn before river")
        self.board.append(card)
        self.street = 'river'

    def get_all_known_cards(self) -> List[Card]:
        known = []
        for hand in self.player_hands:
            known.extend(hand)
        known.extend(self.board)
        return known

    def calculate_equities(self, num_sims: int = 10_000, seed: int = None) -> Dict[int, float]:
        """
        Calculate win probability for each player.

        Args:
            num_sims: Number of Monte Carlo simulations
            seed: Random seed for reproducibility

        Returns:
            Dict mapping player index (0-based) to equity (0.0-1.0)
        """
        if len(self.player_hands) != self.num_players:
            raise ValueError(f"Expected {self.num_players} players, got {len(self.player_hands)}")

        if seed is not None:
            random.seed(seed)

        if len(self.board) == 5:
            return self._calculate_exact_equities()

        win_counts = [0.0] * self.num_players
        cards_needed = 5 - len(self.board)

        for _ in range(num_sims):
            deck = Deck()
            deck.shuffle()

            known_cards = self.get_all_known_cards()
            for card in known_cards:
                for i, deck_card in enumerate(deck._cards):
                    if deck_card.rank == card.rank and deck_card.suit == card.suit:
                        deck._cards.pop(i)
                        break

            # Complete the board
            remaining_board = [deck.deal_one() for _ in range(cards_needed)]
            full_board = self.board + remaining_board

            # Evaluate all hands
            strengths = []
            for player_hand in self.player_hands:
                strength = evaluate(player_hand + full_board)
                strengths.append(strength)

            # Determine winner(s)
            max_strength = max(strengths)
            winners = [i for i, s in enumerate(strengths) if s == max_strength]

            # Award equity (split if tie)
            equity_per_winner = 1.0 / len(winners)
            for winner_idx in winners:
                win_counts[winner_idx] += equity_per_winner

        equities = {i: count / num_sims for i, count in enumerate(win_counts)}
        return equities

    def _calculate_exact_equities(self) -> Dict[int, float]:
        strengths = []
        for player_hand in self.player_hands:
            strength = evaluate(player_hand + self.board)
            strengths.append(strength)

        max_strength = max(strengths)
        winners = [i for i, s in enumerate(strengths) if s == max_strength]

        equities = {}
        for i in range(self.num_players):
            if i in winners:
                equities[i] = 1.0 / len(winners)
            else:
                equities[i] = 0.0

        return equities


def parse_card_string(card_str: str) -> Card:
    if len(card_str) != 2:
        if card_str.startswith('10'):  # just one obvious case where it just feels bad to type Th, not 10h
            card_str = "T" + card_str[2]
        else:
            raise ValueError(f"Card string must be 2 characters, got: {card_str}")

    rank = card_str[0].upper()
    suit = card_str[1].lower()

    valid_ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    valid_suits = ['s', 'h', 'd', 'c']

    if rank not in valid_ranks:
        raise ValueError(f"Invalid rank: {rank}")
    if suit not in valid_suits:
        raise ValueError(f"Invalid suit: {suit}")

    return Card(rank, suit)


def parse_cards_string(cards_str: str) -> List[Card]:
    """
    Parse a space-separated string of cards.

    Args:
        cards_str: Space-separated card strings (e.g., 'As Kh')

    Returns:
        List of Card objects

    Examples:
        'As Kh' → [Card('A', 's'), Card('K', 'h')]
        'Qd Qs' → [Card('Q', 'd'), Card('Q', 's')]
    """
    card_strings = cards_str.strip().split()
    return [parse_card_string(cs) for cs in card_strings]
