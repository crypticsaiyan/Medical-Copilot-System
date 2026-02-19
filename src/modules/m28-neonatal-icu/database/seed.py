"""
database/seed.py
────────────────
Module 28 — Neonatal ICU Monitoring System

Applies JSON Schema validation to all 5 collections, then inserts
realistic sample documents so the Streamlit dashboard has data to display.

Run once (or whenever you want a clean demo state):
    python -m database.seed          # from src/modules/m28-neonatal-icu/
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running directly: python database/seed.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.connection import (
    db,
    neonates_col,
    admissions_col,
    observations_col,
    devices_col,
    vital_signs_col,
)
from database.schema import apply_schemas

# ── Helpers ───────────────────────────────────────────────────────────────────

UTC = timezone.utc


def _dt(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    return datetime.now(UTC) - timedelta(days=days_ago, hours=hours_ago)


# ── Sample documents ──────────────────────────────────────────────────────────

NEONATES = [
    {
        "neonate_id":             "N001",
        "name":                   "Arjun Mehta",
        "dob":                    _dt(days_ago=10),
        "blood_group":            "B+",
        "gestational_age_weeks":  30,
        "gender":                 "Male",
        "birth_weight_g":         1450,
    },
    {
        "neonate_id":             "N002",
        "name":                   "Priya Sharma",
        "dob":                    _dt(days_ago=5),
        "blood_group":            "A+",
        "gestational_age_weeks":  28,
        "gender":                 "Female",
        "birth_weight_g":         980,
    },
    {
        "neonate_id":             "N003",
        "name":                   "Rohan Das",
        "dob":                    _dt(days_ago=2),
        "blood_group":            "O+",
        "gestational_age_weeks":  34,
        "gender":                 "Male",
        "birth_weight_g":         2100,
    },
]

ADMISSIONS = [
    {
        "admission_id":    "ADM001",
        "neonate_id":      "N001",
        "admission_date":  _dt(days_ago=10),
        "bed_no":          "B-01",
        "diagnosis":       "Respiratory Distress Syndrome",
        "status":          "Admitted",
    },
    {
        "admission_id":    "ADM002",
        "neonate_id":      "N002",
        "admission_date":  _dt(days_ago=5),
        "bed_no":          "B-02",
        "diagnosis":       "Extreme Prematurity",
        "status":          "Admitted",
    },
    {
        "admission_id":    "ADM003",
        "neonate_id":      "N003",
        "admission_date":  _dt(days_ago=2),
        "bed_no":          "B-03",
        "diagnosis":       "Neonatal Jaundice",
        "status":          "Admitted",
    },
]

DEVICES = [
    {
        "device_id":       "DEV001",
        "device_type":     "Pulse Oximeter",
        "manufacturer":    "Nellcor",
        "model_number":    "PM10N",
        "last_calibrated": _dt(days_ago=30),
        "status":          "Active",
    },
    {
        "device_id":       "DEV002",
        "device_type":     "Cardiorespiratory Monitor",
        "manufacturer":    "Philips",
        "model_number":    "MX40",
        "last_calibrated": _dt(days_ago=15),
        "status":          "Active",
    },
    {
        "device_id":       "DEV003",
        "device_type":     "Incubator Monitor",
        "manufacturer":    "Dräger",
        "model_number":    "Caleo",
        "last_calibrated": _dt(days_ago=7),
        "status":          "Active",
    },
]

# Realistic NICU vital signs — some intentionally out-of-range to trigger alerts
VITALS = [
    # ADM001 — multiple readings over 2 hours
    {"record_id": "VS001", "admission_id": "ADM001", "device_id": "DEV001",
     "record_time": _dt(hours_ago=12), "heart_rate": 148, "spo2": 95,
     "respiratory_rate": 52, "temp": 36.8, "systolic_bp": 48, "diastolic_bp": 30},
    {"record_id": "VS002", "admission_id": "ADM001", "device_id": "DEV001",
     "record_time": _dt(hours_ago=10), "heart_rate": 185, "spo2": 88,   # ← ALERT: HR high, SpO2 low
     "respiratory_rate": 70, "temp": 38.1, "systolic_bp": 50, "diastolic_bp": 32},
    {"record_id": "VS003", "admission_id": "ADM001", "device_id": "DEV002",
     "record_time": _dt(hours_ago=8), "heart_rate": 155, "spo2": 93,
     "respiratory_rate": 58, "temp": 37.0, "systolic_bp": 46, "diastolic_bp": 28},
    {"record_id": "VS004", "admission_id": "ADM001", "device_id": "DEV002",
     "record_time": _dt(hours_ago=4), "heart_rate": 162, "spo2": 91,
     "respiratory_rate": 62, "temp": 36.9, "systolic_bp": 49, "diastolic_bp": 31},
    {"record_id": "VS005", "admission_id": "ADM001", "device_id": "DEV001",
     "record_time": _dt(hours_ago=1), "heart_rate": 145, "spo2": 96,
     "respiratory_rate": 50, "temp": 36.7, "systolic_bp": 52, "diastolic_bp": 33},

    # ADM002
    {"record_id": "VS006", "admission_id": "ADM002", "device_id": "DEV002",
     "record_time": _dt(hours_ago=5), "heart_rate": 130, "spo2": 92,
     "respiratory_rate": 48, "temp": 36.5, "systolic_bp": 44, "diastolic_bp": 28},
    {"record_id": "VS007", "admission_id": "ADM002", "device_id": "DEV003",
     "record_time": _dt(hours_ago=2), "heart_rate": 92,  "spo2": 89,   # ← ALERT: HR low, SpO2 low
     "respiratory_rate": 45, "temp": 35.9, "systolic_bp": 42, "diastolic_bp": 26},

    # ADM003
    {"record_id": "VS008", "admission_id": "ADM003", "device_id": "DEV001",
     "record_time": _dt(hours_ago=3), "heart_rate": 155, "spo2": 97,
     "respiratory_rate": 44, "temp": 37.2, "systolic_bp": 55, "diastolic_bp": 35},
]

OBSERVATIONS = [
    {"observation_id": "OBS001", "admission_id": "ADM001",
     "observation_time": _dt(hours_ago=11), "feeding_status": "IV Nutrition",
     "crying_level": "Mild", "notes": "Baby appears pale, mild subcostal recession noted."},
    {"observation_id": "OBS002", "admission_id": "ADM001",
     "observation_time": _dt(hours_ago=6), "feeding_status": "IV Nutrition",
     "crying_level": "Moderate", "notes": "O2 saturation improved after CPAP adjustment."},
    {"observation_id": "OBS003", "admission_id": "ADM002",
     "observation_time": _dt(hours_ago=4), "feeding_status": "Formula",
     "crying_level": "High", "notes": "Poor sucking reflex. Weight gain: +12g today."},
    {"observation_id": "OBS004", "admission_id": "ADM003",
     "observation_time": _dt(hours_ago=2), "feeding_status": "Breastfed",
     "crying_level": "None", "notes": "Jaundice improving under phototherapy. Bilirubin trending down."},
]


# ── Main seeding routine ──────────────────────────────────────────────────────

def seed(*, drop_existing: bool = True) -> None:
    """Apply schema validation then insert sample documents."""

    print("\n[seed] ── Applying JSON Schema validators ──")
    apply_schemas(db, verbose=True)

    collections_data = [
        (neonates_col,     NEONATES,     "neonates"),
        (admissions_col,   ADMISSIONS,   "nicu_admissions"),
        (devices_col,      DEVICES,      "monitoring_devices"),
        (vital_signs_col,  VITALS,       "vital_signs_records"),
        (observations_col, OBSERVATIONS, "nurse_observations"),
    ]

    print("\n[seed] ── Seeding collections ──")
    for col, docs, name in collections_data:
        if drop_existing:
            col.delete_many({})  # Clear existing data
        result = col.insert_many(docs)
        print(f"  ✅  Inserted {len(result.inserted_ids)} docs into '{name}'")

    print("\n[seed] 🎉 Database seeded successfully.")
    print(f"[seed]    Database : {db.name}")
    print(f"[seed]    Collections: {db.list_collection_names()}")


if __name__ == "__main__":
    seed()
