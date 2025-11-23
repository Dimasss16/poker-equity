# Poker Equity Calculator

Texas Hold'em equity calculator using Monte Carlo simulation. Computes pre-flop hand rankings and live odds as community cards are revealed.

Supports the following:

- Real-time equity updates through preflop -> flop -> turn -> river
- 2-6 players dynamic probabilities updates with folding functionality
- Visual poker table with auto-calculating equity

## Usage

### Web App

```bash
python app.py
```

Opens at `http://localhost:5003`. Enter hole cards for each player; equity calculates automatically as you add board cards.

### live odds

```bash
python scripts/live_odds_cli.py
```


## Dependencies

- Python 3.8+
- eval7
- Flask
- pandas, matplotlib, tqdm
