"""
database/connection.py
──────────────────────
Module 28 — Neonatal ICU Monitoring System

Singleton MongoDB connection for the NICU module.
Resolves the .env file relative to THIS file so cwd doesn't matter.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

# ── Locate and load .env (always relative to this file) ──────────────────────
_MODULE_ROOT = Path(__file__).resolve().parents[1]   # m28-neonatal-icu/
_local_env   = _MODULE_ROOT / ".env"

if _local_env.exists():
    load_dotenv(_local_env)
else:
    load_dotenv()   # fallback: walk upward until a .env is found

# ── Read config ───────────────────────────────────────────────────────────────
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME: str   = os.getenv("DB_NAME", "nicu_db")

# ── Build client (module-level singleton) ─────────────────────────────────────
try:
    _client: MongoClient = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=8_000,
        connectTimeoutMS=8_000,
    )
    # Eagerly ping so failure surfaces at import time.
    _client.admin.command("ping")
except (ConnectionFailure, ConfigurationError) as exc:
    print(f"[NICU-M28] ❌ MongoDB connection failed: {exc}", file=sys.stderr)
    print(
        "[NICU-M28] Hint: copy .env.example → .env and set MONGO_URI.",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

# ── Database handle ───────────────────────────────────────────────────────────
db = _client[DB_NAME]

# ── Named collection handles (used by backend modules) ───────────────────────
neonates_col      = db["neonates"]
admissions_col    = db["nicu_admissions"]
observations_col  = db["nurse_observations"]
devices_col       = db["monitoring_devices"]
vital_signs_col   = db["vital_signs_records"]


def get_collection(name: str):
    """Return any collection from the NICU database by name."""
    return db[name]


def ping() -> bool:
    """Return True if MongoDB is reachable."""
    try:
        _client.admin.command("ping")
        return True
    except Exception:
        return False


if __name__ == "__main__":
    status = "✅ Connected" if ping() else "❌ Unreachable"
    print(f"[NICU-M28] MongoDB status: {status}")
    print(f"[NICU-M28] Database      : {DB_NAME}")
    print(f"[NICU-M28] Collections   : {db.list_collection_names()}")
