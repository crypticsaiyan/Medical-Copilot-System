"""
backend/analytics.py
─────────────────────
Module 28 — Neonatal ICU Monitoring System

Aggregation Pipelines that SIMULATE MongoDB Views.

In a relational DBMS you'd create a VIEW with CREATE VIEW. MongoDB Atlas
supports read-only views via db.createView(), but here we expose the same
pipelines as Python functions so the Streamlit UI can display both the
pipeline definition and the resulting data — satisfying the "show DBMS
mechanics" requirement.

Functions
─────────
  vital_signs_summary_view(admission_id)  → avg/min/max stats per admission
  daily_admissions_view()                 → admission count grouped by date
  alert_vitals_view(admission_id)         → records outside safe thresholds
  neonate_admission_join_view()           → $lookup join (simulates SQL JOIN)
"""

from __future__ import annotations

from database.connection import admissions_col, vital_signs_col


# ── View 1: Vital Signs Summary ────────────────────────────────────────────────

def vital_signs_summary_view(admission_id: str) -> tuple[list[dict], list[dict]]:
    """
    Aggregation pipeline that computes avg / min / max for key vitals.
    Simulates:
        CREATE VIEW v_vital_summary AS
        SELECT admission_id,
               AVG(heart_rate), MIN(heart_rate), MAX(heart_rate), ...
        FROM vital_signs_records GROUP BY admission_id;
    """
    pipeline = [
        {"$match": {"admission_id": admission_id}},
        {
            "$group": {
                "_id": "$admission_id",
                "avg_heart_rate":       {"$avg": "$heart_rate"},
                "min_heart_rate":       {"$min": "$heart_rate"},
                "max_heart_rate":       {"$max": "$heart_rate"},
                "avg_spo2":             {"$avg": "$spo2"},
                "min_spo2":             {"$min": "$spo2"},
                "avg_respiratory_rate": {"$avg": "$respiratory_rate"},
                "avg_temp":             {"$avg": "$temp"},
                "total_readings":       {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "admission_id":         "$_id",
                "avg_heart_rate":       {"$round": ["$avg_heart_rate", 1]},
                "min_heart_rate":       1,
                "max_heart_rate":       1,
                "avg_spo2":             {"$round": ["$avg_spo2", 1]},
                "min_spo2":             1,
                "avg_respiratory_rate": {"$round": ["$avg_respiratory_rate", 1]},
                "avg_temp":             {"$round": ["$avg_temp", 2]},
                "total_readings":       1,
            }
        },
    ]
    results = list(vital_signs_col.aggregate(pipeline))
    return results, pipeline


# ── View 2: Daily Admissions Count ────────────────────────────────────────────

def daily_admissions_view() -> tuple[list[dict], list[dict]]:
    """
    Aggregation pipeline counting admissions per calendar day.
    Simulates:
        CREATE VIEW v_daily_admissions AS
        SELECT DATE(admission_date) AS day, COUNT(*) AS total
        FROM nicu_admissions GROUP BY day ORDER BY day;
    """
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$admission_date"}
                },
                "total_admissions": {"$sum": 1},
                "diagnoses":        {"$push": "$diagnosis"},
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "date":             "$_id",
                "total_admissions": 1,
                "diagnoses":        1,
            }
        },
    ]
    results = list(admissions_col.aggregate(pipeline))
    return results, pipeline


# ── View 3: Alert Vitals (out-of-range readings) ──────────────────────────────

# NICU normal ranges
THRESHOLDS = {
    "heart_rate":       {"min": 100, "max": 180},
    "spo2":             {"min": 90,  "max": 100},
    "respiratory_rate": {"min": 30,  "max": 60},
    "temp":             {"min": 36.5,"max": 37.5},
}


def alert_vitals_view(admission_id: str) -> tuple[list[dict], list[dict]]:
    """
    Returns vital-sign records where any reading falls outside safe thresholds.
    Simulates:
        CREATE VIEW v_vital_alerts AS
        SELECT * FROM vital_signs_records
        WHERE heart_rate < 100 OR heart_rate > 180
           OR spo2 < 90 OR temp NOT BETWEEN 36.5 AND 37.5 ...;
    """
    pipeline = [
        {"$match": {"admission_id": admission_id}},
        {
            "$match": {
                "$or": [
                    {"heart_rate":       {"$lt": THRESHOLDS["heart_rate"]["min"]}},
                    {"heart_rate":       {"$gt": THRESHOLDS["heart_rate"]["max"]}},
                    {"spo2":             {"$lt": THRESHOLDS["spo2"]["min"]}},
                    {"respiratory_rate": {"$lt": THRESHOLDS["respiratory_rate"]["min"]}},
                    {"respiratory_rate": {"$gt": THRESHOLDS["respiratory_rate"]["max"]}},
                    {"temp":             {"$lt": THRESHOLDS["temp"]["min"]}},
                    {"temp":             {"$gt": THRESHOLDS["temp"]["max"]}},
                ]
            }
        },
        {"$sort": {"record_time": -1}},
        {"$project": {"_id": 0}},
    ]
    results = list(vital_signs_col.aggregate(pipeline))
    return results, pipeline


# ── View 4: Neonate–Admission Join ($lookup) ──────────────────────────────────

def neonate_admission_join_view() -> tuple[list[dict], list[dict]]:
    """
    $lookup pipeline joining nicu_admissions → neonates.
    Simulates:
        CREATE VIEW v_admission_summary AS
        SELECT a.*, n.name, n.gestational_age_weeks, n.birth_weight_g
        FROM nicu_admissions a
        JOIN neonates n ON a.neonate_id = n.neonate_id
        WHERE a.status = 'Admitted';
    """
    pipeline = [
        {"$match": {"status": "Admitted"}},
        {
            "$lookup": {
                "from":         "neonates",
                "localField":   "neonate_id",
                "foreignField": "neonate_id",
                "as":           "neonate_info",
            }
        },
        {"$unwind": {"path": "$neonate_info", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id":           0,
                "admission_id":  1,
                "bed_no":        1,
                "diagnosis":     1,
                "status":        1,
                "admission_date":1,
                "neonate_id":    1,
                "neonate_name":  "$neonate_info.name",
                "gender":        "$neonate_info.gender",
                "gestational_age_weeks": "$neonate_info.gestational_age_weeks",
                "birth_weight_g":        "$neonate_info.birth_weight_g",
            }
        },
        {"$sort": {"admission_date": -1}},
    ]
    results = list(admissions_col.aggregate(pipeline))
    return results, pipeline
