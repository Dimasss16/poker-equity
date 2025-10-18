#!/usr/bin/env python3
"""
Generate pre-flop equity analysis.

Usage:
    python scripts/generate_heatmap.py [--sims 50000] [--seed 42]
"""

import argparse
from src.preflop import generate_preflop_analysis


def main():
    parser = argparse.ArgumentParser(
        description='Generate pre-flop equity table and heatmaps'
    )
    parser.add_argument(
        '--sims',
        type=int,
        default=50_000,
        help='Number of simulations per hand class (default: 50000)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs',
        help='Output directory (default: outputs)'
    )

    args = parser.parse_args()

    generate_preflop_analysis(
        output_dir=args.output_dir,
        num_sims=args.sims,
        seed=args.seed
    )


if __name__ == '__main__':
    main()