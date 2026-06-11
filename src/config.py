"""Project configuration constants for Phase 1.

Phase 1 intentionally performs no external API calls and requires no secrets.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FIXTURES_DATA_DIR = DATA_DIR / "fixtures"
REPORTS_DATA_DIR = DATA_DIR / "reports"
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TESTS_DIR = PROJECT_ROOT / "tests"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

UTC_TIMEZONE = "UTC"
TAIWAN_TIMEZONE = "Asia/Taipei"
TAIWAN_PREMARKET_CUTOFF = "08:45"
