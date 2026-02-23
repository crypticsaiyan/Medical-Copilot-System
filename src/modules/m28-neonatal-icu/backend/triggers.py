"""
backend/triggers.py
────────────────────
Module 28 — Neonatal ICU Monitoring System

Simulates MongoDB Triggers / Change Streams for vital sign alerting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DBMS CONCEPT EXPLANATION — Triggers vs Change Streams
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
In a relational DBMS you'd write:

    CREATE TRIGGER check_vitals_after_insert
    AFTER INSERT ON vital_signs_records
    FOR EACH ROW
    BEGIN
        IF NEW.heart_rate > 180 OR NEW.spo2 < 90 THEN
            INSERT INTO alerts (...) VALUES (...);
        END IF;
    END;

MongoDB's equivalent is a Change Stream on a collection:

    with vital_signs_col.watch([{"$match": {"operationType": "insert"}}]) as stream:
        for change in stream:
            doc = change["fullDocument"]
            alerts = check_vital_thresholds(doc)
            if alerts:
                send_alert(alerts)

Change Streams require a MongoDB replica set or Atlas cluster (which you
are using). The function `watch_vitals_stream()` below demonstrates this
pattern but is not called automatically — it's shown for DBMS concept credit
and can be run as a background thread.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database.connection import vital_signs_col

UTC = timezone.utc

# ── NICU safe threshold ranges ────────────────────────────────────────────────

THRESHOLDS: dict[str, dict[str, float]] = {
    "heart_rate":       {"min": 100.0, "max": 180.0, "unit": "bpm"},
    "spo2":             {"min": 90.0,  "max": 100.0, "unit": "%"},
    "respiratory_rate": {"min": 30.0,  "max": 60.0,  "unit": "breaths/min"},
    "temp":             {"min": 36.5,  "max": 37.5,  "unit": "°C"},
    "systolic_bp":      {"min": 40.0,  "max": 80.0,  "unit": "mmHg"},
}

SEVERITY_MAP = {
    "heart_rate":       {"critical_low": 80,  "critical_high": 200},
    "spo2":             {"critical_low": 85,  "critical_high": None},
    "respiratory_rate": {"critical_low": 20,  "critical_high": 80},
    "temp":             {"critical_low": 35.5,"critical_high": 38.5},
}


def _severity(field: str, value: float) -> str:
    """Return 'CRITICAL' or 'WARNING' based on how far outside range the value is."""
    crit = SEVERITY_MAP.get(field, {})
    c_low  = crit.get("critical_low")
    c_high = crit.get("critical_high")
    if (c_low is not None and value < c_low) or (c_high is not None and value > c_high):
        return "CRITICAL"
    return "WARNING"


# ── Core trigger logic ────────────────────────────────────────────────────────

def check_vital_thresholds(vital_doc: dict[str, Any]) -> list[dict]:
    """
    Pure function — mimics what the AFTER INSERT trigger body would do.
    Returns a list of alert dicts (empty if all vitals are within range).

    Each alert contains:
        field, value, threshold_min, threshold_max, severity, message
    """
    alerts: list[dict] = []
    ts = vital_doc.get("record_time", datetime.now(UTC))

    for field, bounds in THRESHOLDS.items():
        value = vital_doc.get(field)
        if value is None:
            continue

        low, high = bounds["min"], bounds["max"]
        unit = bounds["unit"]

        if value < low or value > high:
            direction = "LOW ↓" if value < low else "HIGH ↑"
            severity  = _severity(field, float(value))
            label     = field.replace("_", " ").title()
            alerts.append({
                "field":         field,
                "label":         label,
                "value":         value,
                "unit":          unit,
                "direction":     direction,
                "threshold_min": low,
                "threshold_max": high,
                "severity":      severity,
                "admission_id":  vital_doc.get("admission_id", "N/A"),
                "record_time":   str(ts),
                "message": (
                    f"⚠️  [{severity}] {label} is {direction}: "
                    f"{value} {unit} "
                    f"(normal {low}–{high} {unit})"
                ),
            })
    return alerts


def run_trigger_on_all_vitals(admission_id: str) -> tuple[list[dict], str]:
    """
    Pulls all vital records for an admission and runs the threshold
    check on each — simulating a trigger that fired on every INSERT.

    Returns (all_alerts, trigger_code_explanation).
    """
    records  = list(vital_signs_col.find({"admission_id": admission_id}, {"_id": 0}))
    all_alerts: list[dict] = []
    for rec in records:
        all_alerts.extend(check_vital_thresholds(rec))

    trigger_sql_equivalent = (
        "-- Equivalent SQL TRIGGER (for DBMS concept):\n"
        "CREATE TRIGGER check_vitals_after_insert\n"
        "AFTER INSERT ON vital_signs_records\n"
        "FOR EACH ROW\n"
        "BEGIN\n"
        "  IF NEW.heart_rate < 100 OR NEW.heart_rate > 180 THEN\n"
        "    INSERT INTO alerts(field, value, severity) VALUES('heart_rate', NEW.heart_rate, 'WARNING');\n"
        "  END IF;\n"
        "  IF NEW.spo2 < 90 THEN\n"
        "    INSERT INTO alerts(field, value, severity) VALUES('spo2', NEW.spo2, 'CRITICAL');\n"
        "  END IF;\n"
        "  -- ... (similar for temp, resp_rate, bp)\n"
        "END;"
    )
    return all_alerts, trigger_sql_equivalent


def watch_vitals_stream() -> None:
    """
    DEMONSTRATION ONLY — shows how a real MongoDB Change Stream would
    watch for new vital-sign inserts and fire the alert logic.

    Requires: MongoDB Atlas (replica set) — which this project uses.

    To run as a background thread in a real production system:
        import threading
        t = threading.Thread(target=watch_vitals_stream, daemon=True)
        t.start()
    """
    pipeline = [{"$match": {"operationType": "insert"}}]
    print("[trigger] 👀 Watching vital_signs_records for new inserts ...")
    with vital_signs_col.watch(pipeline, full_document="updateLookup") as stream:
        for change in stream:
            doc    = change.get("fullDocument", {})
            alerts = check_vital_thresholds(doc)
            if alerts:
                for alert in alerts:
                    print(f"[trigger] 🚨 ALERT — {alert['message']}")
            else:
                print(f"[trigger] ✅ Vitals normal for admission {doc.get('admission_id')}")
