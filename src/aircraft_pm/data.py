"""Data loading, validation, and RUL label generation for C-MAPSS FD001."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from aircraft_pm.config import (
    DEFAULT_CLIP_RUL,
    RAW_COLUMNS,
    RUL_FILE,
    TEST_FILE,
    TRAIN_FILE,
)


def load_raw_file(file_path: Path) -> pd.DataFrame:
    """Load a space-delimited C-MAPSS data file into a pandas DataFrame.

    Args:
        file_path: Path to the data file.

    Returns:
        DataFrame with RAW_COLUMNS named.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If file structure does not match expected columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    df = pd.read_csv(file_path, sep=r"\s+", header=None)

    # Some raw files have trailing whitespace leading to extra empty columns
    if df.shape[1] > len(RAW_COLUMNS):
        # Drop columns that are completely NaN (usually from trailing spaces)
        df = df.iloc[:, : len(RAW_COLUMNS)]

    if df.shape[1] != len(RAW_COLUMNS):
        raise ValueError(
            f"Expected {len(RAW_COLUMNS)} columns, got {df.shape[1]} from {file_path}"
        )

    df.columns = RAW_COLUMNS
    return df


def validate_dataframe(df: pd.DataFrame, is_test: bool = False) -> Dict[str, Any]:
    """Perform rigorous validation on a loaded C-MAPSS DataFrame.

    Checks:
    - Null / NaN value counts
    - Monotonically increasing cycles per engine
    - Cycle continuity (starts at cycle 1, no duplicate cycles)
    - Row count and unique engine count

    Args:
        df: Input DataFrame.
        is_test: Flag indicating whether dataset is test data.

    Returns:
        Dictionary with validation statistics and status.
    """
    results: Dict[str, Any] = {
        "valid": True,
        "is_test": is_test,
        "rows": len(df),
        "columns": len(df.columns),
        "unique_engines": int(df["engine_id"].nunique()),
        "null_count": int(df.isnull().sum().sum()),
        "cycle_min": int(df["cycle"].min()),
        "cycle_max": int(df["cycle"].max()),
        "issues": [],
    }

    if results["null_count"] > 0:
        results["valid"] = False
        results["issues"].append(f"Found {results['null_count']} null values.")

    # Check each engine's cycle sequence
    for engine_id, group in df.groupby("engine_id"):
        cycles = group["cycle"].values
        if len(cycles) == 0:
            results["valid"] = False
            results["issues"].append(f"Engine {engine_id} has zero records.")
            continue

        if cycles[0] != 1:
            results["valid"] = False
            results["issues"].append(
                f"Engine {engine_id} starts at cycle {cycles[0]}, expected 1."
            )

        # Check monotonic strictly increasing: diff should be all 1s
        diffs = np.diff(cycles)
        if not np.all(diffs == 1):
            results["valid"] = False
            results["issues"].append(
                f"Engine {engine_id} has non-continuous or non-monotonic cycle steps."
            )

    return results


def add_rul_labels(
    df: pd.DataFrame, clip_rul: Optional[int] = DEFAULT_CLIP_RUL
) -> pd.DataFrame:
    """Calculate Remaining Useful Life (RUL) for run-to-failure training data.

    In the training set, each engine runs until failure. The maximum recorded
    cycle T_max represents the failure point.
    RUL at cycle t is defined as:
        RUL(t) = T_max - t
    If clip_rul is specified, a piecewise-linear target is also computed:
        RUL_clipped(t) = min(RUL(t), clip_rul)

    Args:
        df: Run-to-failure training DataFrame.
        clip_rul: Maximum RUL threshold for piecewise degradation.

    Returns:
        DataFrame copy with 'rul' and 'rul_clipped' columns added.
    """
    df_out = df.copy()

    # Calculate max cycle per engine
    max_cycles = df_out.groupby("engine_id")["cycle"].transform("max")
    df_out["rul"] = max_cycles - df_out["cycle"]

    if clip_rul is not None and clip_rul > 0:
        df_out["rul_clipped"] = np.minimum(df_out["rul"], clip_rul)
    else:
        df_out["rul_clipped"] = df_out["rul"]

    return df_out


def load_train_data(
    train_file: Path = TRAIN_FILE, clip_rul: Optional[int] = DEFAULT_CLIP_RUL
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load, validate, and label the training dataset.

    Args:
        train_file: Path to train_FD001.txt.
        clip_rul: Clipping threshold for RUL.

    Returns:
        Tuple of (labeled DataFrame, validation report).
    """
    df = load_raw_file(train_file)
    val_report = validate_dataframe(df, is_test=False)
    if not val_report["valid"]:
        raise ValueError(f"Training data validation failed: {val_report['issues']}")

    df_labeled = add_rul_labels(df, clip_rul=clip_rul)
    return df_labeled, val_report


def load_test_data(
    test_file: Path = TEST_FILE,
    rul_file: Path = RUL_FILE,
    clip_rul: Optional[int] = DEFAULT_CLIP_RUL,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Load, validate test trajectories and official ground-truth test RUL.

    In test_FD001.txt, the time series ends prior to failure.
    RUL_FD001.txt contains the true remaining cycles after the last recorded
    test cycle for each engine.

    Args:
        test_file: Path to test_FD001.txt.
        rul_file: Path to RUL_FD001.txt.
        clip_rul: Threshold to clip test RUL target.

    Returns:
        Tuple of:
          - test_df: Full test trajectory DataFrame.
          - test_last_records: DataFrame containing the final recorded cycle per test engine,
            joined with 'rul' and 'rul_clipped'.
          - val_report: Validation summary.
    """
    test_df = load_raw_file(test_file)
    val_report = validate_dataframe(test_df, is_test=True)
    if not val_report["valid"]:
        raise ValueError(f"Test data validation failed: {val_report['issues']}")

    if not rul_file.exists():
        raise FileNotFoundError(f"Official RUL ground truth file not found: {rul_file}")

    rul_df = pd.read_csv(rul_file, header=None, names=["rul"])
    rul_df["engine_id"] = np.arange(1, len(rul_df) + 1)

    if clip_rul is not None and clip_rul > 0:
        rul_df["rul_clipped"] = np.minimum(rul_df["rul"], clip_rul)
    else:
        rul_df["rul_clipped"] = rul_df["rul"]

    # Extract the last record for each engine in test_df
    last_records = test_df.groupby("engine_id").last().reset_index()
    test_last_records = pd.merge(last_records, rul_df, on="engine_id", how="left")

    return test_df, test_last_records, val_report
