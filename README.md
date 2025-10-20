# Poker Equity Calculator

This is a Texas Hold'em equity calculator that computes winning probabilities using Monte Carlo simulation. We calculate both static pre-flop hand rankings and dynamic live odds as community cards are revealed.

## Overview

We calculate probabilities for a given hand through statistical sampling. For pre-flop, we evaluate all 169 unique starting hand combinations against random opponents. For live play, we track how win probabilities change during each round as more cards are revealed.

## How It Works

### Probability Calculation

The system calculates equity by simulating random board cards and evaluating the resulting 7-card hands (2 hole cards + 5 community cards). 

To evaluate pre-flop equity of a particular hand, we sample random board cards, give random cards to our opponent (for this we assume there's only one, as we wanna get the best estimation -- optimistic), and then imagine we both went all-in pre-flop. So we just evaluate the 7-card hands we get. To calibrate the probabilities, we repeat the experiment 50000 times.

For example, to find pocket aces' pre-flop equity:

1. Deal ourselves pocket aces
2. Deal opponent random cards  
3. Deal random board cards
4. Evaluate both 7-card hands using `eval7` library
5. Repeat 50,000 times and count wins/ties

The equity is simply: `(wins + 0.5 * ties) / total_simulations`

### Dynamic Probability Updates

For this part, we need to update probabilities, but we need less simulations as community cards appear. 

The `LiveOddsCalculator` handles this progression, filtering known cards from the deck before each simulation to ensure mathematically valid results.

### Percentile Calculation

Pre-flop hand percentiles account for both equity and combination frequency. While there are 169 theoretical hand classes, some represent more actual combinations:

- Pocket pairs: 6 combinations each
- Suited hands: 4 combinations each  
- Offsuit hands: 12 combinations each

Percentiles rank all 1,326 possible starting hands from strongest to weakest, showing what percentage of hands are stronger than yours. The heatmaps showing this can be found in `src/outputs/`.

## Folding Functionality

We also allow players to fold at any time like it happens in real games. When a player folds, their hand is removed from equity calculations.
After displaying equity, the calculator prompts for fold commands (typing `f2`, `f3`, `f4` folds the respective player). When a fold occurs, equity recalculates for remaining players. Folded players display with zero percent equity and a `[FOLDED]` marker.

Folded cards are treated as dead money that cannot win or appear on future community cards.
Multiple players can fold sequentially. If four players start and two fold on the flop, turn equity calculations only consider the remaining two players. Their combined equity always sums to one hundred percent. The system prevents folding when only one player remains.
Fold decisions are permanent and irreversible. A player who folds pocket aces that would have made a full house still receives zero equity. The calculator analyzes decisions rather than enforcing game rules.

## Usage

### Live Odds Calculator

Run the interactive calculator:
```bash
python scripts/live_odds_cli.py
```

### Pre-flop Analysis

Generate hand ranking heatmaps:
```bash
python scripts/generate_heatmap.py
```
