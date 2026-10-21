"""Configuration constants, file paths, and column schemas for C-MAPSS FD001."""

from pathlib import Path
from typing import Dict, List

# Directory Paths
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# File Paths for FD001
TRAIN_FILE = DATA_RAW_DIR / "train_FD001.txt"
TEST_FILE = DATA_RAW_DIR / "test_FD001.txt"
RUL_FILE = DATA_RAW_DIR / "RUL_FD001.txt"

# Column Schema
INDEX_COLUMNS: List[str] = ["engine_id", "cycle"]
SETTING_COLUMNS: List[str] = ["setting_1", "setting_2", "setting_3"]
SENSOR_COLUMNS: List[str] = [f"sensor_{i}" for i in range(1, 22)]
RAW_COLUMNS: List[str] = INDEX_COLUMNS + SETTING_COLUMNS + SENSOR_COLUMNS

# In FD001 (Sea Level, single fault HPC degradation), these sensors/settings have zero or near-zero variance
CONSTANT_OR_LOW_VARIANCE_COLS: List[str] = [
    "setting_3",
    "sensor_1",
    "sensor_5",
    "sensor_10",
    "sensor_16",
    "sensor_18",
    "sensor_19",
]

INFORMATIVE_SENSOR_COLS: List[str] = [
    col for col in SENSOR_COLUMNS if col not in CONSTANT_OR_LOW_VARIANCE_COLS
]

# Physical sensor descriptions from NASA C-MAPSS documentation
SENSOR_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "setting_1": {"name": "Altitude / Mach", "unit": "-", "desc": "Operating condition setting 1"},
    "setting_2": {"name": "Mach / Condition", "unit": "-", "desc": "Operating condition setting 2"},
    "setting_3": {"name": "TRA (Throttle)", "unit": "-", "desc": "Throttle Resolver Angle (constant 100)"},
    "sensor_1": {"name": "T2 (Total Temp at Fan Inlet)", "unit": "°R", "desc": "Fan inlet temperature (constant 518.67)"},
    "sensor_2": {"name": "T24 (LPC Outlet Temp)", "unit": "°R", "desc": "Total temperature at Low Pressure Compressor outlet"},
    "sensor_3": {"name": "T30 (HPC Outlet Temp)", "unit": "°R", "desc": "Total temperature at High Pressure Compressor outlet"},
    "sensor_4": {"name": "T50 (LPT Outlet Temp)", "unit": "°R", "desc": "Total temperature at Low Pressure Turbine outlet"},
    "sensor_5": {"name": "P2 (Fan Inlet Pressure)", "unit": "psia", "desc": "Total pressure at fan inlet (constant 14.62)"},
    "sensor_6": {"name": "P15 (Bypass Duct Pressure)", "unit": "psia", "desc": "Total pressure in bypass-duct"},
    "sensor_7": {"name": "P30 (HPC Outlet Pressure)", "unit": "psia", "desc": "Total pressure at High Pressure Compressor outlet"},
    "sensor_8": {"name": "Nf (Physical Fan Speed)", "unit": "rpm", "desc": "Physical rotational speed of fan"},
    "sensor_9": {"name": "Nc (Physical Core Speed)", "unit": "rpm", "desc": "Physical rotational speed of core"},
    "sensor_10": {"name": "epr (Engine Pressure Ratio)", "unit": "-", "desc": "Engine pressure ratio P50/P2 (constant 1.3)"},
    "sensor_11": {"name": "Ps30 (HPC Outlet Static Pressure)", "unit": "psia", "desc": "Static pressure at High Pressure Compressor outlet"},
    "sensor_12": {"name": "Phi (Fuel Flow Ratio)", "unit": "pps/psi", "desc": "Ratio of fuel flow to Ps30"},
    "sensor_13": {"name": "NRf (Corrected Fan Speed)", "unit": "rpm", "desc": "Corrected rotational speed of fan"},
    "sensor_14": {"name": "NRc (Corrected Core Speed)", "unit": "rpm", "desc": "Corrected rotational speed of core"},
    "sensor_15": {"name": "BPR (Bypass Ratio)", "unit": "-", "desc": "Ratio of bypass airflow to core airflow"},
    "sensor_16": {"name": "farB (Burner Fuel-Air Ratio)", "unit": "-", "desc": "Burner fuel-air ratio (constant 0.03)"},
    "sensor_17": {"name": "htBleed (Bleed Enthalpy)", "unit": "-", "desc": "Bleed enthalpy"},
    "sensor_18": {"name": "Nf_dmd (Demanded Fan Speed)", "unit": "rpm", "desc": "Demanded fan speed (constant 2388)"},
    "sensor_19": {"name": "PCNfR_dmd (Demanded Corrected Fan Speed)", "unit": "rpm", "desc": "Demanded corrected fan speed (constant 100.0)"},
    "sensor_20": {"name": "W31 (HPT Coolant Bleed)", "unit": "lbm/s", "desc": "High Pressure Turbine coolant bleed flow"},
    "sensor_21": {"name": "W32 (LPT Coolant Bleed)", "unit": "lbm/s", "desc": "Low Pressure Turbine coolant bleed flow"},
}

# Modeling Constants
DEFAULT_CLIP_RUL: int = 125
DEFAULT_RANDOM_STATE: int = 42

# Operational Health Thresholds (in cycles of RUL)
HEALTH_CRITICAL: int = 25
HEALTH_WARNING: int = 50

# AeroSentinel Cryptographic Artifact Authentication (Ed25519)
# Trusted production public key (safe to store in configuration).
# Private keys must NEVER be stored in the repository, committed, or bundled.
AEROSENTINEL_ED25519_PUBLIC_KEY: str = (
    "2fc1416b5634cf20e6b403fafc572160b27615adbdf5352458a492d52251e45b"
)
# Secure production startup requires valid Ed25519 signature by default.
# Can be toggled for dev/isolated testing via environment variable.
import os as _os
AEROSENTINEL_REQUIRE_AUTH: bool = _os.getenv(
    "AEROSENTINEL_REQUIRE_AUTH", "1"
).lower() in ("1", "true", "yes")
