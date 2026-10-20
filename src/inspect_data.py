
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "train_FD001.txt"

COLUMNS = [
    "engine_id",
    "cycle",
    "setting_1",
    "setting_2",
    "setting_3",
    *[f"sensor_{i}" for i in range(1, 22)],
]


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}\n"
            "Download and extract CMAPSSData.zip, then place "
            "train_FD001.txt in data/raw/."
        )

    df = pd.read_csv(
        DATA_FILE,
        sep=r"\s+",
        header=None,
        names=COLUMNS,
    )

    print("\n=== AIRCRAFT ENGINE DATA INSPECTION ===")
    print(f"\nDataset path: {DATA_FILE}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Unique engines: {df['engine_id'].nunique()}")
    print(
        "Cycle range:",
        f"{df['cycle'].min()} to {df['cycle'].max()}",
    )

    print("\n=== FIRST FIVE ROWS ===")
    print(df.head().to_string(index=False))

    print("\n=== MISSING VALUES ===")
    print(df.isnull().sum().to_string())

    print("\n=== CYCLES PER ENGINE ===")
    print(
        df.groupby("engine_id")["cycle"]
        .max()
        .describe()
        .to_string()
    )

    print("\n=== DATA TYPES ===")
    print(df.dtypes.to_string())

    print("\nData inspection completed successfully.")


if __name__ == "__main__":
    main()
