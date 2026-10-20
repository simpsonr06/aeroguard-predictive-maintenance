"""Unit tests for data loading, validation, and RUL labeling."""

import numpy as np
import pandas as pd
import pytest

from aircraft_pm.config import RAW_COLUMNS, RUL_FILE, TEST_FILE, TRAIN_FILE
from aircraft_pm.data import (
    add_rul_labels,
    load_raw_file,
    load_test_data,
    load_train_data,
    validate_dataframe,
)


def test_train_file_exists():
    """Ensure the raw training dataset exists."""
    assert TRAIN_FILE.exists(), f"Missing train file: {TRAIN_FILE}"


def test_test_file_exists():
    """Ensure the raw test dataset exists."""
    assert TEST_FILE.exists(), f"Missing test file: {TEST_FILE}"


def test_rul_file_exists():
    """Ensure the raw RUL file exists."""
    assert RUL_FILE.exists(), f"Missing RUL file: {RUL_FILE}"


def test_train_data_loading_and_validation():
    """Verify train data loads correctly and passes validation checks."""
    train_df, report = load_train_data(clip_rul=125)

    assert report["valid"] is True
    assert report["null_count"] == 0
    assert report["unique_engines"] == 100
    assert len(train_df) == 20631
    assert "rul" in train_df.columns
    assert "rul_clipped" in train_df.columns


def test_rul_calculation_logic():
    """Verify RUL calculation rules: monotonically decreasing to 0 at failure cycle."""
    # Create synthetic run-to-failure engine
    df_synth = pd.DataFrame(
        {
            "engine_id": [1, 1, 1, 1, 2, 2, 2],
            "cycle": [1, 2, 3, 4, 1, 2, 3],
        }
    )
    # Add dummy sensors
    for c in RAW_COLUMNS:
        if c not in df_synth.columns:
            df_synth[c] = 0.0

    labeled = add_rul_labels(df_synth, clip_rul=2)

    # Engine 1 runs up to cycle 4: RULs should be 3, 2, 1, 0
    e1_rul = labeled[labeled["engine_id"] == 1]["rul"].values
    assert np.array_equal(e1_rul, [3, 2, 1, 0])

    # Clipped RUL (threshold 2): should be 2, 2, 1, 0
    e1_clipped = labeled[labeled["engine_id"] == 1]["rul_clipped"].values
    assert np.array_equal(e1_clipped, [2, 2, 1, 0])

    # Engine 2 runs up to cycle 3: RULs should be 2, 1, 0
    e2_rul = labeled[labeled["engine_id"] == 2]["rul"].values
    assert np.array_equal(e2_rul, [2, 1, 0])


def test_test_data_loading():
    """Verify test data loading and pairing with ground-truth RUL."""
    test_df, test_last, report = load_test_data(clip_rul=125)

    assert report["valid"] is True
    assert len(test_last) == 100
    assert "rul" in test_last.columns
    assert "rul_clipped" in test_last.columns
    assert test_last["rul"].min() >= 0
