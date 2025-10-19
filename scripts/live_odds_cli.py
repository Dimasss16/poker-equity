from src.live_odds import LiveOddsCalculator, parse_cards_string
from src.deck import Card
from src.evaluator import handtype
from tqdm import tqdm


def format_card(card: Card) -> str:
    suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
    return f"{card.rank}{suit_symbols[card.suit]}"


def format_cards(cards: list) -> str:
    return ' '.join(format_card(c) for c in cards)


def display_equities(calc: LiveOddsCalculator, equities: dict, show_board: bool = True):
    print()
    if show_board and calc.board:
        print(f"Board: {format_cards(calc.board)}")
        print()

    print(f"--- {calc.street.upper()} Equities ---")
    print()

    for player_idx in range(calc.num_players):
        equity = equities[player_idx]
        hand_str = format_cards(calc.player_hands[player_idx])

        is_folded = player_idx in calc.folded_players

        # Show hand type on river
        hand_info = ""
        if len(calc.board) == 5:
            full_hand = calc.player_hands[player_idx] + calc.board
            hand_type = handtype(full_hand)
            hand_info = f" ({hand_type})"
        if is_folded:
            hand_info = " (FOLDED)"

        player_name = "You" if player_idx == 0 else f"Player {player_idx + 1}"

        bar = tqdm.format_meter(
            n=int(equity * 100),
            total=100,
            elapsed=0,
            ncols=60,  # Total width of bar + percentage
            bar_format="{percentage:3.0f}%|{bar}|",
            ascii=False
        )

        print(f"{player_name:10s} [{hand_str}]  {equity * 100:5.1f}%  {bar}{hand_info}")

    print()

def handle_fold_commands(calc: LiveOddsCalculator, next_street: str = "next street") -> bool | None:
    """
    Handle folding.

    Args:
        calc: LiveOddsCalculator instance
        next_street: Name of the next street (e.g., "flop", "turn", "river")

    Returns:
        True if a fold occurred, False if user wants to continue
    """
    active_players = calc.get_active_players()

    # Don't allow folding if only 1 player remains
    if len(active_players) <= 1:
        input("Press Enter to continue...")
        return False

    print("Options:")
    print(f"  [Enter]  - Continue to {next_street}")

    # Show fold options for active players only
    for player_idx in active_players:
        player_name = "You" if player_idx == 0 else f"Player {player_idx + 1}"
        print(f"  [f{player_idx + 1}]    - Fold {player_name}")

    print()

    while True:
        command = input("> ").strip().lower()

        # Empty = continue
        if command == "":
            return False

        # Fold command: f1, f2, f3, etc.
        if command.startswith('f') and len(command) == 2 and command[1].isdigit():
            try:
                player_num = int(command[1])
                player_idx = player_num - 1

                # Try to fold
                calc.fold_player(player_idx)

                player_name = "You" if player_idx == 0 else f"Player {player_num}"
                hand_str = format_cards(calc.player_hands[player_idx])
                print(f"\n{player_name} folds [{hand_str}]\n")

                return True

            except ValueError as e:
                print(f"  {e}")
                continue
            except Exception as e:
                print(f"  Error: {e}")
                continue

        print("  Invalid command. Press Enter to continue or 'f#' to fold a player.")


def main():
    print("="*30)
    print("Live poker odds calculator")
    print("="*30)
    print()
    print("Calculate real-time equity as the hand progresses.")
    print("All players' hole cards must be known.")
    print()

    # Get number of players
    while True:
        try:
            num_players = int(input("How many players? (2-6): ").strip())
            if 2 <= num_players <= 6:
                break
            print("Please enter a number between 2 and 6")
        except ValueError:
            print("Please enter a valid number")

    print()
    calc = LiveOddsCalculator(num_players)

    # Input hole cards for each player
    print("Enter hole cards for each player (format: As Kh)")
    print()

    for i in range(num_players):
        while True:
            try:
                player_name = "You" if i == 0 else f"Player {i + 1}"
                cards_input = input(f"{player_name}: ").strip()
                cards = parse_cards_string(cards_input)

                if len(cards) != 2:
                    print("Please enter exactly 2 cards")
                    continue

                calc.add_player_hand(cards)
                print(f"{format_cards(cards)}")
                break
            except Exception as e:
                print(f"Error: {e}")

    # Calculate pre-flop equities
    print("="*30)
    print("Calculating pre-flop equities")
    print("="*30)
    # Pre-flop
    print("Simulating 50,000 random boards...")

    equities = calc.calculate_equities(num_sims=50_000)
    display_equities(calc, equities, show_board=False)

    # Allow folding pre-flop
    while handle_fold_commands(calc, "the flop"):
        print("=" * 30)
        print("Updated pre-flop equities")
        print("=" * 30)
        print("Recalculating with remaining players...")
        equities = calc.calculate_equities(num_sims=50_000)
        display_equities(calc, equities, show_board=False)

    print()
    while True:
        try:
            flop_input = input("Enter flop (3 cards, e.g., Kc 7d 2h): ").strip()
            flop = parse_cards_string(flop_input)

            if len(flop) != 3:
                print("Flop must be exactly 3 cards")
                continue

            calc.deal_flop(flop)
            print(f"Flop: {format_cards(flop)}")
            break
        except Exception as e:
            print(f"Error: {e}")

    print("="*30)
    print("Calculating flop equities")
    print("="*30)
    print("Simulating 50,000 turn/river combinations...")
    # Flop
    equities = calc.calculate_equities(num_sims=50_000)
    display_equities(calc, equities)

    # Allow folding on flop
    while handle_fold_commands(calc, next_street="the turn"):
        print("=" * 30)
        print("Updated flop equities")
        print("=" * 30)
        print("Recalculating with remaining players...")
        equities = calc.calculate_equities(num_sims=50_000)
        display_equities(calc, equities)

    # Deal turn
    print()
    while True:
        try:
            turn_input = input("Enter turn (1 card): ").strip()
            turn = parse_cards_string(turn_input)

            if len(turn) != 1:
                print("Turn must be exactly 1 card")
                continue

            calc.deal_turn(turn[0])
            print(f"  Turn: {format_cards([turn[0]])}")
            break
        except Exception as e:
            print(f"Error: {e}")

    print("="*30)
    print("Calculating turn equities")
    print("="*30)
    print("Simulating 10,000 river cards...")

    equities = calc.calculate_equities(num_sims=10_000)
    display_equities(calc, equities)

    # Allow folding on turn
    while handle_fold_commands(calc, next_street="the river"):
        print("=" * 30)
        print("Updated turn equities")
        print("=" * 30)
        print("Recalculating with remaining players...")
        equities = calc.calculate_equities(num_sims=10_000)
        display_equities(calc, equities)

    # Deal river
    print()
    while True:
        try:
            river_input = input("Enter river (1 card): ").strip()
            river = parse_cards_string(river_input)

            if len(river) != 1:
                print("  River must be exactly 1 card")
                continue

            calc.deal_river(river[0])
            print(f"  River: {format_cards([river[0]])}")
            break
        except Exception as e:
            print(f"  Error: {e}")

    print("Final results:")
    equities = calc.calculate_equities()
    display_equities(calc, equities)

    winner_idx = max(equities, key=equities.get)
    winner_name = "You" if winner_idx == 0 else f"Player {winner_idx + 1}"

    if equities[winner_idx] == 1.0:
        if winner_name == "You":
            print("You win!")
        else:
            print(f"{winner_name} wins!")
    else:
        # Split pot
        winners = [i for i, eq in equities.items() if eq > 0]
        winner_names = ["You" if i == 0 else f"Player {i + 1}" for i in winners]
        print(f"Split pot between: {', '.join(winner_names)}")

    print()
    print()


if __name__ == '__main__':
    main()
    # TODO: add probability of split and show when non-zero
