"""
_path_setup.py
──────────────
Adds the m28-neonatal-icu module root to sys.path so that
  `from database.connection import ...`
  `from backend.admissions import ...`
work regardless of the cwd Streamlit / Python is run from.

Import this at the top of any entry-point script.
"""
import sys
from pathlib import Path

_MODULE_ROOT = Path(__file__).resolve().parent  # …/m28-neonatal-icu/

if str(_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE_ROOT))
