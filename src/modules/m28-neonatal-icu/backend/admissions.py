"""
backend/admissions.py
─────────────────────
Module 28 — Neonatal ICU Monitoring System

CRUD operations for Neonate and NICU_ADMISSION entities.
Every public function returns a tuple:
    (result, raw_query)
so the Streamlit UI can display the exact MongoDB query that was executed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from database.connection import neonates_col, admissions_col

UTC = timezone.utc


# ── Neonate CRUD ──────────────────────────────────────────────────────────────

def add_neonate(
    name: str,
    dob: datetime,
    blood_group: str,
    gestational_age_weeks: int,
    gender: str,
    birth_weight_g: float,
    neonate_id: str | None = None,
) -> tuple[dict, dict]:
    """Insert a new neonate document. Returns (inserted_doc, raw_query)."""
    doc = {
        "neonate_id":            neonate_id or f"N{uuid.uuid4().hex[:6].upper()}",
        "name":                  name,
        "dob":                   dob,
        "blood_group":           blood_group,
        "gestational_age_weeks": int(gestational_age_weeks),
        "gender":                gender,
        "birth_weight_g":        float(birth_weight_g),
        "created_at":            datetime.now(UTC),
    }
    raw_query = {
        "operation":   "insert_one",
        "collection":  "neonates",
        "document":    {k: str(v) if isinstance(v, datetime) else v for k, v in doc.items()},
    }
    neonates_col.insert_one(doc)
    return doc, raw_query


def get_neonate(neonate_id: str) -> tuple[dict | None, dict]:
    """Fetch a single neonate by ID."""
    query = {"neonate_id": neonate_id}
    raw_query = {"operation": "find_one", "collection": "neonates", "filter": query}
    result = neonates_col.find_one(query, {"_id": 0})
    return result, raw_query


def get_all_neonates() -> tuple[list[dict], dict]:
    """Return all neonate documents."""
    raw_query = {"operation": "find", "collection": "neonates", "filter": {}, "projection": {"_id": 0}}
    results = list(neonates_col.find({}, {"_id": 0}))
    return results, raw_query


# ── NICU Admission CRUD ───────────────────────────────────────────────────────

def admit_neonate(
    neonate_id: str,
    bed_no: str,
    diagnosis: str,
    admission_date: datetime | None = None,
    admission_id: str | None = None,
) -> tuple[dict, dict]:
    """Create a new NICU admission record."""
    doc = {
        "admission_id":   admission_id or f"ADM{uuid.uuid4().hex[:6].upper()}",
        "neonate_id":     neonate_id,
        "admission_date": admission_date or datetime.now(UTC),
        "bed_no":         bed_no,
        "diagnosis":      diagnosis,
        "status":         "Admitted",
        "created_at":     datetime.now(UTC),
    }
    raw_query = {
        "operation":  "insert_one",
        "collection": "nicu_admissions",
        "document":   {k: str(v) if isinstance(v, datetime) else v for k, v in doc.items()},
    }
    admissions_col.insert_one(doc)
    return doc, raw_query


def get_active_admissions() -> tuple[list[dict], dict]:
    """Return all currently admitted neonates."""
    query = {"status": "Admitted"}
    raw_query = {
        "operation":  "find",
        "collection": "nicu_admissions",
        "filter":     query,
        "projection": {"_id": 0},
        "sort":       {"admission_date": -1},
    }
    results = list(admissions_col.find(query, {"_id": 0}).sort("admission_date", -1))
    return results, raw_query


def get_admission(admission_id: str) -> tuple[dict | None, dict]:
    """Fetch a single admission by ID."""
    query = {"admission_id": admission_id}
    raw_query = {"operation": "find_one", "collection": "nicu_admissions", "filter": query}
    result = admissions_col.find_one(query, {"_id": 0})
    return result, raw_query


def get_admissions_for_neonate(neonate_id: str) -> tuple[list[dict], dict]:
    """All admissions for a specific neonate (current + historical)."""
    query = {"neonate_id": neonate_id}
    raw_query = {
        "operation":  "find",
        "collection": "nicu_admissions",
        "filter":     query,
        "sort":       {"admission_date": -1},
    }
    results = list(admissions_col.find(query, {"_id": 0}).sort("admission_date", -1))
    return results, raw_query


def discharge_neonate(admission_id: str) -> tuple[dict, dict]:
    """Update admission status to Discharged."""
    query  = {"admission_id": admission_id}
    update = {"$set": {"status": "Discharged", "discharged_at": datetime.now(UTC)}}
    raw_query = {
        "operation":  "update_one",
        "collection": "nicu_admissions",
        "filter":     query,
        "update":     update,
    }
    result = admissions_col.update_one(query, update)
    return {"matched": result.matched_count, "modified": result.modified_count}, raw_query
