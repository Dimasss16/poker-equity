from src.equity import compute_heads_up_equity


def main():
    print("Testing known equity values...")
    print(f"AA:  {compute_heads_up_equity('AA',  num_sims=50000, seed=42):.2%}")
    print(f"KK:  {compute_heads_up_equity('KK',  num_sims=50000, seed=42):.2%}")
    print(f"AKs: {compute_heads_up_equity('AKs', num_sims=50000, seed=42):.2%}")
    print(f"72o: {compute_heads_up_equity('72o', num_sims=50000, seed=42):.2%}")


if __name__ == "__main__":
    main()
