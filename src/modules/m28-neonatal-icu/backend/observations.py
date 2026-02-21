"""
backend/observations.py
────────────────────────
Module 28 — Neonatal ICU Monitoring System

CRUD operations for Nurse_Observation entity.
Returns (result, raw_query) tuples for transparent UI display.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from database.connection import observations_col

UTC = timezone.utc


def log_observation(
    admission_id: str,
    feeding_status: str,
    crying_level: str,
    notes: str = "",
    observation_time: datetime | None = None,
    observation_id: str | None = None,
) -> tuple[dict, dict]:
    """Insert a new nurse observation for an admission."""
    doc = {
        "observation_id":   observation_id or f"OBS{uuid.uuid4().hex[:6].upper()}",
        "admission_id":     admission_id,
        "observation_time": observation_time or datetime.now(UTC),
        "feeding_status":   feeding_status,
        "crying_level":     crying_level,
        "notes":            notes,
        "created_at":       datetime.now(UTC),
    }
    raw_query = {
        "operation":  "insert_one",
        "collection": "nurse_observations",
        "document":   {k: str(v) if isinstance(v, datetime) else v for k, v in doc.items()},
    }
    observations_col.insert_one(doc)
    return doc, raw_query


def get_observations_for_admission(admission_id: str) -> tuple[list[dict], dict]:
    """Fetch all nurse observations for an admission, sorted chronologically."""
    query = {"admission_id": admission_id}
    raw_query = {
        "operation":  "find",
        "collection": "nurse_observations",
        "filter":     query,
        "sort":       {"observation_time": 1},
        "projection": {"_id": 0},
    }
    results = list(observations_col.find(query, {"_id": 0}).sort("observation_time", 1))
    return results, raw_query


def get_latest_observation(admission_id: str) -> tuple[dict | None, dict]:
    """Fetch only the most recent observation for an admission."""
    query = {"admission_id": admission_id}
    raw_query = {
        "operation":  "find_one",
        "collection": "nurse_observations",
        "filter":     query,
        "sort":       {"observation_time": -1},
    }
    result = observations_col.find_one(query, {"_id": 0}, sort=[("observation_time", -1)])
    return result, raw_query


def get_all_observations() -> tuple[list[dict], dict]:
    """Fetch all observations across all admissions (admin view)."""
    raw_query = {
        "operation":  "find",
        "collection": "nurse_observations",
        "filter":     {},
        "sort":       {"observation_time": -1},
    }
    results = list(observations_col.find({}, {"_id": 0}).sort("observation_time", -1))
    return results, raw_query
