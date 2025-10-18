from dataclasses import dataclass
from typing import List
import random


@dataclass(frozen=True)
class Card:
    """
    Represents a single playing card.

    Attributes:
        rank: Card rank ('A', 'K', 'Q', 'J', 'T', '9', ..., '2')
        suit: Card suit ('s'=spades, 'h'=hearts, 'd'=diamonds, 'c'=clubs)
    """
    rank: str
    suit: str

    def __str__(self) -> str:
        suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
        return f"{self.rank}{suit_symbols.get(self.suit, self.suit)}"

    def __repr__(self) -> str:
        return f"Card('{self.rank}', '{self.suit}')"


class Deck:
    RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    SUITS = ['s', 'h', 'd', 'c']

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self._cards: List[Card] = [
            Card(rank, suit)
            for suit in self.SUITS
            for rank in self.RANKS
        ]

    def shuffle(self, seed: int = None) -> None:
        if seed is not None:
            random.seed(seed)
        random.shuffle(self._cards)

    def deal_one(self) -> Card:
        if not self._cards:
            raise IndexError("Cannot deal from an empty deck")
        return self._cards.pop()

    def cards_remaining(self) -> int:
        return len(self._cards)

    def is_empty(self) -> bool:
        return len(self._cards) == 0

    def __len__(self) -> int:
        return len(self._cards)

    def __str__(self) -> str:
        return f"Deck({len(self._cards)} cards remaining)"