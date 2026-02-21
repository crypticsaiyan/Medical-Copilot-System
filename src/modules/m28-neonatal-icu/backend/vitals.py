"""
backend/vitals.py
─────────────────
Module 28 — Neonatal ICU Monitoring System

CRUD operations for Vital_Signs_Record entity.
Returns (result, raw_query) tuples.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from database.connection import vital_signs_col

UTC = timezone.utc


def log_vitals(
    admission_id: str,
    device_id: str,
    heart_rate: float,
    spo2: float,
    respiratory_rate: float,
    temp: float,
    systolic_bp: float | None = None,
    diastolic_bp: float | None = None,
    record_time: datetime | None = None,
    record_id: str | None = None,
) -> tuple[dict, dict]:
    """Insert a single vital-signs reading."""
    doc: dict[str, Any] = {
        "record_id":        record_id or f"VS{uuid.uuid4().hex[:6].upper()}",
        "admission_id":     admission_id,
        "device_id":        device_id,
        "record_time":      record_time or datetime.now(UTC),
        "heart_rate":       float(heart_rate),
        "spo2":             float(spo2),
        "respiratory_rate": float(respiratory_rate),
        "temp":             float(temp),
        "created_at":       datetime.now(UTC),
    }
    if systolic_bp is not None:
        doc["systolic_bp"] = float(systolic_bp)
    if diastolic_bp is not None:
        doc["diastolic_bp"] = float(diastolic_bp)

    raw_query = {
        "operation":  "insert_one",
        "collection": "vital_signs_records",
        "document":   {k: str(v) if isinstance(v, datetime) else v for k, v in doc.items()},
    }
    vital_signs_col.insert_one(doc)
    return doc, raw_query


def get_vitals_for_admission(admission_id: str) -> tuple[list[dict], dict]:
    """All vital-sign records for an admission, time-ordered ascending."""
    query = {"admission_id": admission_id}
    raw_query = {
        "operation":  "find",
        "collection": "vital_signs_records",
        "filter":     query,
        "sort":       {"record_time": 1},
        "projection": {"_id": 0},
    }
    results = list(vital_signs_col.find(query, {"_id": 0}).sort("record_time", 1))
    return results, raw_query


def get_latest_vitals(admission_id: str) -> tuple[dict | None, dict]:
    """The single most recent vital-signs reading for an admission."""
    query = {"admission_id": admission_id}
    raw_query = {
        "operation":  "find_one",
        "collection": "vital_signs_records",
        "filter":     query,
        "sort":       {"record_time": -1},
    }
    result = vital_signs_col.find_one(query, {"_id": 0}, sort=[("record_time", -1)])
    return result, raw_query


def get_all_vitals() -> tuple[list[dict], dict]:
    """All vital records across all admissions (for dashboard overview)."""
    raw_query = {
        "operation":  "find",
        "collection": "vital_signs_records",
        "filter":     {},
        "sort":       {"record_time": -1},
    }
    results = list(vital_signs_col.find({}, {"_id": 0}).sort("record_time", -1))
    return results, raw_query
