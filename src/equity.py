from typing import List
import random
from src.deck import Deck, Card
from src.evaluator import evaluate
from src.utils import sample_hand_from_class


def compute_heads_up_equity(
        hand_class: str,
        num_sims: int = 50_000,
        seed: int = None
) -> float:
    """
    Compute heads-up all-in equity for a starting hand class.

    Simulates dealing hero a hand from hand_class, villain random cards,
    and a 5-card board, then evaluates who wins. Repeats num_sims times.

    Args:
        hand_class: Hand class like "AA", "AKs", "72o"
        num_sims: Number of Monte Carlo simulations
        seed: Optional random seed for reproducibility

    Returns:
        Equity as a float between 0 and 1 (e.g., 0.85 = 85% equity)
    """
    if seed is not None:
        random.seed(seed)

    total_score = 0.0

    for _ in range(num_sims):
        deck = Deck()
        deck.shuffle()

        hero_hand = sample_hand_from_class(hand_class, excluded_cards=[])

        # Remove hero cards from deck like it would happened during dealing
        for card in hero_hand:
            for i, deck_card in enumerate(deck._cards):
                if deck_card.rank == card.rank and deck_card.suit == card.suit:
                    deck._cards.pop(i)
                    break

        # Deal villain hand (2 cards)
        villain_hand = [deck.deal_one(), deck.deal_one()]

        # Deal board (5 cards)
        board = [deck.deal_one() for _ in range(5)]

        # Evaluate both hands
        hero_strength = evaluate(hero_hand + board)
        villain_strength = evaluate(villain_hand + board)

        # Score the result
        if hero_strength > villain_strength:
            total_score += 1.0
        elif hero_strength == villain_strength:
            total_score += 0.5
        # else: loss, add 0, so we do nothing

    return total_score / num_sims


def compute_equity_vs_hand(
        hero_hand: List[Card],
        villain_hand: List[Card],
        known_board: List[Card] = None,
        num_sims: int = 10_000,
        seed: int = None
) -> float:
    """
    Compute equity for specific hole cards with optional known board cards.

    Useful for "live odds" calculation during a hand.

    Args:
        hero_hand: Hero's 2 hole cards
        villain_hand: Villain's 2 hole cards
        known_board: Already-dealt board cards (0-5 cards)
        num_sims: Number of simulations
        seed: Optional random seed

    Returns:
        Hero's equity (0.0 to 1.0)
    """
    if known_board is None:
        known_board = []

    if len(hero_hand) != 2 or len(villain_hand) != 2:
        raise ValueError("Hero and villain must each have exactly 2 cards")

    if len(known_board) > 5:
        raise ValueError("Board cannot have more than 5 cards")

    if seed is not None:
        random.seed(seed)

    if len(known_board) == 5:
        hero_strength = evaluate(hero_hand + known_board)
        villain_strength = evaluate(villain_hand + known_board)

        if hero_strength > villain_strength:
            return 1.0
        elif hero_strength == villain_strength:
            return 0.5
        else:
            return 0.0

    total_score = 0.0
    cards_needed = 5 - len(known_board)

    for _ in range(num_sims):
        deck = Deck()
        deck.shuffle()

        # Remove hero, villain, and known board cards
        all_known = hero_hand + villain_hand + known_board
        for card in all_known:
            for i, deck_card in enumerate(deck._cards):
                if deck_card.rank == card.rank and deck_card.suit == card.suit:
                    deck._cards.pop(i)
                    break

        # Complete the board
        remaining_board = [deck.deal_one() for _ in range(cards_needed)]
        full_board = known_board + remaining_board

        # Evaluate
        hero_strength = evaluate(hero_hand + full_board)
        villain_strength = evaluate(villain_hand + full_board)

        if hero_strength > villain_strength:
            total_score += 1.0
        elif hero_strength == villain_strength:
            total_score += 0.5

    return total_score / num_sims