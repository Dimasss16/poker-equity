from typing import List, Tuple
import random
from src.deck import Card


RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
SUITS = ['s', 'h', 'd', 'c']


def parse_hand_class(hand_class: str) -> Tuple[str, str, bool]:
    hand_class = hand_class.strip().upper()

    if len(hand_class) < 2 or len(hand_class) > 3:
        raise ValueError(f"Invalid hand class format: {hand_class}")

    rank1 = hand_class[0]
    rank2 = hand_class[1]

    if rank1 not in RANKS or rank2 not in RANKS:
        raise ValueError(f"Invalid ranks in hand class: {hand_class}")

    # Pairs
    if rank1 == rank2:
        if len(hand_class) == 3:
            raise ValueError(f"Pairs cannot have suited/offsuit modifier: {hand_class}")
        return (rank1, rank2, None)

    # Suited or offsuit
    if len(hand_class) == 3:
        modifier = hand_class[2].lower()
        if modifier == 's':
            return (rank1, rank2, True)
        elif modifier == 'o':
            return (rank1, rank2, False)
        else:
            raise ValueError(f"Invalid suited/offsuit modifier: {modifier}")
    else:
        raise ValueError(f"Non-pair hands must specify 's' or 'o': {hand_class}")


def sample_hand_from_class(hand_class: str, excluded_cards: List[Card] = None) -> List[Card]:
    """
    Sample a random hand from a hand class.
    
    Args:
        hand_class: Hand class like "AKs", "72o", "AA"
        excluded_cards: Cards that are already dealt (cannot be sampled)
        
    Returns:
        List of 2 cards
        
    Raises:
        ValueError: If no valid combos available
        
    Examples:
        "AKs" → [A♠, K♠] or [A♥, K♥] or [A♦, K♦] or [A♣, K♣]
        "AA" → [A♠, A♥] or [A♠, A♦] or ... (6 possible combos)
        "72o" → [7♠, 2♥] or [7♥, 2♠] or ... (12 possible combos)
    """
    rank1, rank2, is_suited = parse_hand_class(hand_class)

    if excluded_cards is None:
        excluded_cards = []

    excluded_set = set((c.rank, c.suit) for c in excluded_cards)

    # Generate all possible combos for this hand class
    possible_hands = []

    if is_suited is None:  # Pair
        # All combinations of 2 different suits
        for i, suit1 in enumerate(SUITS):
            for suit2 in SUITS[i + 1:]:
                card1 = (rank1, suit1)
                card2 = (rank1, suit2)
                if card1 not in excluded_set and card2 not in excluded_set:
                    possible_hands.append([Card(rank1, suit1), Card(rank1, suit2)])

    elif is_suited:  # Suited
        # Both cards same suit
        for suit in SUITS:
            card1 = (rank1, suit)
            card2 = (rank2, suit)
            if card1 not in excluded_set and card2 not in excluded_set:
                possible_hands.append([Card(rank1, suit), Card(rank2, suit)])

    else:  # Offsuit
        # Different suits
        for suit1 in SUITS:
            for suit2 in SUITS:
                if suit1 != suit2:
                    card1 = (rank1, suit1)
                    card2 = (rank2, suit2)
                    if card1 not in excluded_set and card2 not in excluded_set:
                        possible_hands.append([Card(rank1, suit1), Card(rank2, suit2)])

    if not possible_hands:
        raise ValueError(f"No valid combinations available for {hand_class} with given exclusions")

    return random.choice(possible_hands)


def get_combo_count(hand_class: str) -> int:
    _, _, is_suited = parse_hand_class(hand_class)

    if is_suited is None:  # Pair
        return 6
    elif is_suited:  # Suited
        return 4
    else:  # Offsuit
        return 12
