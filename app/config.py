"""
Central place for constants and settings. Kept as plain Python for v1 -
swap for pydantic-settings / environment-driven config once this moves
past a single-developer prototype.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

TARIFF_SLABS_PATH = DATA_DIR / "tariff_slabs.json"
SUBSIDY_RULES_PATH = DATA_DIR / "subsidy_rules.json"

# Illustrative installed-cost assumption (Rs per kW, before subsidy).
# Real installer quotes vary by city, panel brand, and mounting type -
# this is a placeholder default, not a quote. Override per-assessment
# once you have real vendor pricing data.
DEFAULT_SYSTEM_COST_PER_KW = 62500

# Standard residential panel footprint assumption (metres).
PANEL_WIDTH_M = 1.0
PANEL_LENGTH_M = 1.7

# Derates applied in the yield model (Stage 5).
DEFAULT_SOILING_DERATE = 0.97   # dust/soiling losses
DEFAULT_INVERTER_DERATE = 0.96  # inverter + wiring losses
DEFAULT_DEGRADATION_RATE = 0.005  # annual panel output degradation

# Design assumption for shadow-casting (Stage 3): winter solstice,
# the worst-case day for sun angle in the northern hemisphere.
SHADOW_DESIGN_MONTH_DAY = (12, 21)
SHADOW_DESIGN_HOURS = ("09:00", "15:00")
