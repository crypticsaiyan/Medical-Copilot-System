"""
database/schema.py
──────────────────
Module 28 — Neonatal ICU Monitoring System

Defines MongoDB JSON Schema validators for all 5 ER-diagram entities and
provides a helper to apply them to the target database.

Collections created / validated
────────────────────────────────
  neonates               → Neonate
  nicu_admissions        → NICU_ADMISSION
  nurse_observations     → Nurse_Observation
  monitoring_devices     → Monitoring_Device
  vital_signs_records    → Vital_Signs_Record
"""

from __future__ import annotations

from pymongo.database import Database
from pymongo.errors import CollectionInvalid, OperationFailure

# ── Per-collection $jsonSchema validators ─────────────────────────────────────

NEONATE_SCHEMA: dict = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["neonate_id", "name", "dob", "gender", "gestational_age_weeks", "birth_weight_g"],
        "additionalProperties": True,
        "properties": {
            "neonate_id": {
                "bsonType": "string",
                "description": "Unique neonate identifier — required string",
            },
            "name": {
                "bsonType": "string",
                "description": "Full name of the neonate",
            },
            "dob": {
                "bsonType": "date",
                "description": "Date of birth (BSON Date)",
            },
            "blood_group": {
                "bsonType": "string",
                "enum": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"],
                "description": "ABO + Rh blood group",
            },
            "gestational_age_weeks": {
                "bsonType": "int",
                "minimum": 22,
                "maximum": 45,
                "description": "Gestational age in completed weeks",
            },
            "gender": {
                "bsonType": "string",
                "enum": ["Male", "Female", "Other"],
            },
            "birth_weight_g": {
                "bsonType": ["int", "double"],
                "minimum": 300,
                "description": "Birth weight in grams",
            },
        },
    }
}

NICU_ADMISSION_SCHEMA: dict = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["admission_id", "neonate_id", "admission_date", "bed_no", "diagnosis"],
        "additionalProperties": True,
        "properties": {
            "admission_id": {"bsonType": "string"},
            "neonate_id":   {"bsonType": "string", "description": "FK → neonates.neonate_id"},
            "admission_date": {"bsonType": "date"},
            "bed_no": {
                "bsonType": "string",
                "description": "NICU bed identifier, e.g. 'B-04'",
            },
            "diagnosis": {"bsonType": "string"},
            "status": {
                "bsonType": "string",
                "enum": ["Admitted", "Discharged", "Transferred"],
                "description": "Current admission status",
            },
        },
    }
}

NURSE_OBSERVATION_SCHEMA: dict = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["observation_id", "admission_id", "observation_time", "feeding_status", "crying_level"],
        "additionalProperties": True,
        "properties": {
            "observation_id":   {"bsonType": "string"},
            "admission_id":     {"bsonType": "string", "description": "FK → nicu_admissions.admission_id"},
            "observation_time": {"bsonType": "date"},
            "feeding_status": {
                "bsonType": "string",
                "enum": ["Breastfed", "Formula", "IV Nutrition", "NPO", "Mixed"],
            },
            "crying_level": {
                "bsonType": "string",
                "enum": ["None", "Mild", "Moderate", "High"],
            },
            "notes": {"bsonType": "string"},
        },
    }
}

MONITORING_DEVICE_SCHEMA: dict = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["device_id", "device_type", "manufacturer", "model_number"],
        "additionalProperties": True,
        "properties": {
            "device_id":      {"bsonType": "string"},
            "device_type":    {"bsonType": "string"},
            "manufacturer":   {"bsonType": "string"},
            "model_number":   {"bsonType": "string"},
            "last_calibrated": {"bsonType": "date"},
            "status": {
                "bsonType": "string",
                "enum": ["Active", "Maintenance", "Retired"],
            },
        },
    }
}

VITAL_SIGNS_SCHEMA: dict = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "record_id", "admission_id", "device_id", "record_time",
            "heart_rate", "spo2", "respiratory_rate", "temp",
        ],
        "additionalProperties": True,
        "properties": {
            "record_id":         {"bsonType": "string"},
            "admission_id":      {"bsonType": "string", "description": "FK → nicu_admissions.admission_id"},
            "device_id":         {"bsonType": "string", "description": "FK → monitoring_devices.device_id"},
            "record_time":       {"bsonType": "date"},
            "heart_rate": {
                "bsonType": ["int", "double"],
                "minimum": 0,
                "description": "Heart rate in bpm",
            },
            "spo2": {
                "bsonType": ["int", "double"],
                "minimum": 0,
                "maximum": 100,
                "description": "Oxygen saturation %",
            },
            "respiratory_rate": {
                "bsonType": ["int", "double"],
                "minimum": 0,
                "description": "Breaths per minute",
            },
            "temp": {
                "bsonType": ["int", "double"],
                "description": "Body temperature in °C",
            },
            "systolic_bp": {
                "bsonType": ["int", "double"],
                "description": "Systolic blood pressure mmHg",
            },
            "diastolic_bp": {
                "bsonType": ["int", "double"],
                "description": "Diastolic blood pressure mmHg",
            },
        },
    }
}

# ── Registry: (collection_name, validator_dict) ───────────────────────────────
COLLECTION_SCHEMAS: list[tuple[str, dict]] = [
    ("neonates",            NEONATE_SCHEMA),
    ("nicu_admissions",     NICU_ADMISSION_SCHEMA),
    ("nurse_observations",  NURSE_OBSERVATION_SCHEMA),
    ("monitoring_devices",  MONITORING_DEVICE_SCHEMA),
    ("vital_signs_records", VITAL_SIGNS_SCHEMA),
]


# ── Public helper ─────────────────────────────────────────────────────────────

def apply_schemas(database: Database, *, verbose: bool = True) -> None:
    """
    Create each collection (if it doesn't exist) and apply / update
    its JSON Schema validator.

    Safe to call multiple times — uses collMod to update existing
    collections and suppresses CollectionInvalid on first creation.
    """
    existing = set(database.list_collection_names())

    for col_name, validator in COLLECTION_SCHEMAS:
        if col_name not in existing:
            try:
                database.create_collection(col_name, validator={"$jsonSchema": validator["$jsonSchema"]})
                if verbose:
                    print(f"  [schema] ✅  Created '{col_name}' with validator")
            except CollectionInvalid:
                pass  # Race condition — another process created it first
        else:
            # Try to update the validator on existing collections via collMod.
            # Atlas free-tier / restricted users may not have this privilege —
            # in that case we silently skip (validator was already set at creation).
            try:
                database.command(
                    "collMod",
                    col_name,
                    validator={"$jsonSchema": validator["$jsonSchema"]},
                    validationLevel="moderate",
                    validationAction="warn",
                )
                if verbose:
                    print(f"  [schema] 🔄  Updated validator on existing '{col_name}'")
            except OperationFailure:
                if verbose:
                    print(f"  [schema] ℹ️   '{col_name}' exists — collMod skipped (validator set at creation)")

    # Ensure compound indexes useful for DBMS joins / aggregation
    _create_indexes(database, verbose=verbose)


def _create_indexes(database: Database, *, verbose: bool = True) -> None:
    """Create indexes that simulate foreign-key lookup efficiency."""
    index_map = {
        "nicu_admissions":     [("neonate_id",   1)],
        "nurse_observations":  [("admission_id", 1)],
        "vital_signs_records": [("admission_id", 1), ("device_id", 1), ("record_time", -1)],
        "monitoring_devices":  [("device_type",  1)],
    }
    for col_name, fields in index_map.items():
        col = database[col_name]
        for field, direction in fields:
            col.create_index([(field, direction)], background=True)
        if verbose:
            print(f"  [index]  📌  Indexes ensured on '{col_name}'")
