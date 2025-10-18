from typing import List
import eval7
from src.deck import Card


def evaluate(cards: List[Card]) -> int:
    """
    Evaluate a 7-card poker hand.

    Args:
        cards: Exactly 7 cards (2 hole + 5 board)

    Returns:
        Integer rank where HIGHER = STRONGER

    Raises:
        ValueError: If not exactly 7 cards
    """
    if len(cards) != 7:
        raise ValueError(f"Expected exactly 7 cards, got {len(cards)}")

    eval7_cards = [eval7.Card(f"{c.rank}{c.suit}") for c in cards]

    return eval7.evaluate(eval7_cards)


def handtype(cards: List[Card]) -> str:
    rank = evaluate(cards)
    return eval7.handtype(rank)


def compare(hand1: List[Card], hand2: List[Card]) -> int:
    """
    Compare two 7-card hands.

    Args:
        hand1: First hand
        hand2: Second hand

    Returns:
        -1 if hand1 wins, 0 if tie, 1 if hand2 wins
    """
    rank1 = evaluate(hand1)
    rank2 = evaluate(hand2)

    if rank1 > rank2:
        return -1
    elif rank1 < rank2:
        return 1
    else:
        return 0