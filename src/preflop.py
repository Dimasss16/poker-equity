import os
from typing import List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from src.equity import compute_multiway_equity
from src.utils import get_combo_count, RANKS


def generate_all_hand_classes() -> List[str]:
    """
    Generate all 169 unique starting hand classes.

    Returns:
        List of hand class strings

    Format:
        - Pairs: AA, KK, QQ, ..., 22
        - Suited: AKs, AQs, ..., 32s (upper triangle)
        - Offsuit: AKo, AQo, ..., 32o (lower triangle)
    """
    hand_classes = []

    for i, rank1 in enumerate(RANKS):
        for j, rank2 in enumerate(RANKS):
            if i < j:  # Suited (rank1 > rank2)
                hand_classes.append(f"{rank1}{rank2}s")
            elif i > j:  # Offsuit (rank1 < rank2, flip order)
                hand_classes.append(f"{rank2}{rank1}o")
            else:  # Pair
                hand_classes.append(f"{rank1}{rank1}")

    return hand_classes


def compute_all_equities(
        num_players: int = 6,
        num_sims: int = 50_000,
        seed: int = 42
) -> pd.DataFrame:
    """
    Compute multi-player equity for all 169 hand classes.

    Args:
        num_players: Total number of players (default 6 for typical poker game)
        num_sims: Number of Monte Carlo simulations per hand
        seed: Random seed for reproducibility

    Returns:
        DataFrame with columns: hand_class, equity, combos
    """
    hand_classes = generate_all_hand_classes()
    results = []
    num_opponents = num_players - 1

    print(f"Computing equity for {len(hand_classes)} hand classes")
    print(f"Game type: {num_players}-player poker (1 vs {num_opponents} opponents)")
    print(f"Simulations per hand: {num_sims:,}\n")

    for hand_class in tqdm(hand_classes, desc="Computing equities", unit="hand"):
        equity = compute_multiway_equity(
            hand_class,
            num_opponents=num_opponents,
            num_sims=num_sims,
            seed=seed
        )
        combos = get_combo_count(hand_class)

        results.append({
            'hand_class': hand_class,
            'equity': equity,
            'combos': combos
        })

    df = pd.DataFrame(results)
    print("\nEquity computation complete!\n")

    return df


def calculate_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate combo-weighted percentiles for hand classes.

    Args:
        df: DataFrame with columns: hand_class, equity, combos

    Returns:
        DataFrame with added 'percentile' column

    By percentile here we mean "This hand is stronger than X% of all 1,326 combos"

    Algorithm:
        1. Sort hands by equity (strongest first)
        2. Calculate cumulative combo count
        3. Percentile = (midpoint of combo range) / 1326 * 100
    """
    df_sorted = df.sort_values('equity', ascending=False).copy()

    df_sorted['cumulative_combos'] = df_sorted['combos'].cumsum()

    df_sorted['percentile'] = (
            (df_sorted['cumulative_combos'] - df_sorted['combos'] / 2) / 1326 * 100
    )
    return df_sorted[['hand_class', 'equity', 'combos', 'percentile']]


def create_grid_matrix(df: pd.DataFrame, value_column: str) -> np.ndarray:
    """
    Convert DataFrame to 13x13 matrix for heatmap.

    Args:
        df: DataFrame with hand_class and value column
        value_column: 'equity' or 'percentile'

    Returns:
        13x13 numpy array where:
        - Diagonal = pairs (AA, KK, ..., 22)
        - Upper triangle = suited hands
        - Lower triangle = offsuit hands
    """
    matrix = np.zeros((13, 13))
    value_dict = dict(zip(df['hand_class'], df[value_column]))

    for i, rank1 in enumerate(RANKS):
        for j, rank2 in enumerate(RANKS):
            if i == j:
                hand_class = f"{rank1}{rank1}"
            elif i < j:
                hand_class = f"{rank1}{rank2}s"
            else:
                hand_class = f"{rank2}{rank1}o"

            matrix[i, j] = value_dict.get(hand_class, 0)

    return matrix

def plot_heatmap(
        matrix: np.ndarray,
        title: str,
        output_path: str,
        is_percentile: bool = False
):
    fig, ax = plt.subplots(figsize=(14, 14))

    # We use colormap with red to blue with strong contrast, reverse for percentiles
    cmap = plt.get_cmap('RdBu' if is_percentile else 'RdBu_r')
    im = ax.imshow(matrix, cmap=cmap, aspect='auto')
    label = 'Percentile (%)' if is_percentile else 'Equity (%)'
    plt.colorbar(im, ax=ax, label=label)

    for i in range(13):
        for j in range(13):
            rank1, rank2 = RANKS[i], RANKS[j]
            if i == j:
                label = f"{rank1}{rank1}"
            elif i < j:
                label = f"{rank1}{rank2}s"
            else:
                label = f"{rank2}{rank1}o"

            value = matrix[i, j]
            value_text = f"{value:.1f}%"

            threshold = matrix.max() * 0.5
            text_color = 'white' if value < threshold else 'black'

            ax.text(j, i, f"{label}\n{value_text}",
                    ha='center', va='center',
                    fontsize=7, color=text_color, weight='bold')

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=18, pad=20, weight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def main():
    OUTPUT_DIR = 'outputs'
    NUM_PLAYERS = 6
    NUM_SIMS = 50_000
    SEED = 42

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 20)
    print("Pre-flop Multi-Player Equities")
    print("=" * 60)
    print(f"Number of players: {NUM_PLAYERS}")
    print(f"Simulations per hand: {NUM_SIMS:,}")
    print(f"Random seed: {SEED}")
    print(f"Output directory: {OUTPUT_DIR}/")
    print("=" * 20)
    print()

    # Compute equities
    print("Step 1/5: Computing equities for all 169 hand classes...")
    df = compute_all_equities(num_players=NUM_PLAYERS, num_sims=NUM_SIMS, seed=SEED)

    # Calculate percentiles
    print("Step 2/5: Calculating combo-weighted percentiles...")
    df = calculate_percentiles(df)

    # Save CSV
    print("Step 3/5: Saving data table...")
    csv_path = os.path.join(OUTPUT_DIR, f'preflop_equity_table_{NUM_PLAYERS}player.csv')
    df.to_csv(csv_path, index=False, float_format='%.4f')

    # Equity heatmap
    print("Step 4/5: Generating equity heatmap...")
    equity_matrix = create_grid_matrix(df, 'equity') * 100
    plot_heatmap(
        equity_matrix,
        title=f'Pre-Flop {NUM_PLAYERS}-Player Equity (%)',
        output_path=os.path.join(OUTPUT_DIR, f'preflop_equity_heatmap_{NUM_PLAYERS}player.png'),
        is_percentile=False
    )
    print()

    # Percentile heatmap
    print("Step 5/5: Generating percentile heatmap...")
    percentile_matrix = create_grid_matrix(df, 'percentile')
    plot_heatmap(
        percentile_matrix,
        title=f'Pre-Flop Hand Strength Percentile - {NUM_PLAYERS} Players (%)',
        output_path=os.path.join(OUTPUT_DIR, f'preflop_percentile_heatmap_{NUM_PLAYERS}player.png'),
        is_percentile=True
    )
    print()

    print("\n" + "=" * 20)
    print("Results")
    print("=" * 20)
    print(f"\nTop 5 hands by equity ({NUM_PLAYERS}-player):")
    top5 = df.nlargest(5, 'equity')[['hand_class', 'equity', 'percentile']]
    for _, row in top5.iterrows():
        print(f"  {row['hand_class']:4s}  {row['equity']*100:5.2f}%  (percentile: {row['percentile']:5.2f}%)")

    print(f"\nBottom 5 hands by equity ({NUM_PLAYERS}-player):")
    bottom5 = df.nsmallest(5, 'equity')[['hand_class', 'equity', 'percentile']]
    for _, row in bottom5.iterrows():
        print(f"  {row['hand_class']:4s}  {row['equity']*100:5.2f}%  (percentile: {row['percentile']:5.2f}%)")

    print("\n" + "=" * 40)


if __name__ == '__main__':
    main()