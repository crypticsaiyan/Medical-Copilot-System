"""
frontend/components/trigger_alerts.py
──────────────────────────────────────
Renders the Trigger Simulation tab.
Shows:
  - The equivalent SQL TRIGGER code
  - The MongoDB Change Stream pattern
  - Live alert output from checking existing vitals
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from backend.triggers import run_trigger_on_all_vitals, THRESHOLDS


def render_trigger_alerts(admission_id: str) -> None:
    """Display trigger concept explanation and live alert results."""

    st.subheader("⚠️ Trigger Simulation — Vital Sign Alerts")

    # ── Concept explanation ───────────────────────────────────────────────────
    with st.expander("📚 DBMS Concept: Triggers → MongoDB Change Streams", expanded=True):
        st.markdown("""
**In a Relational DBMS**, a trigger fires automatically after an INSERT/UPDATE:
```sql
CREATE TRIGGER check_vitals_after_insert
AFTER INSERT ON vital_signs_records
FOR EACH ROW
BEGIN
  IF NEW.heart_rate < 100 OR NEW.heart_rate > 180 THEN
    INSERT INTO alerts(field, value, severity) VALUES('heart_rate', NEW.heart_rate, 'WARNING');
  END IF;
  IF NEW.spo2 < 90 THEN
    INSERT INTO alerts(field, value, severity) VALUES('spo2', NEW.spo2, 'CRITICAL');
  END IF;
END;
```

**MongoDB equivalent** uses a **Change Stream** on Atlas (replica set):
```python
pipeline = [{"$match": {"operationType": "insert"}}]
with vital_signs_col.watch(pipeline) as stream:
    for change in stream:
        doc = change["fullDocument"]
        alerts = check_vital_thresholds(doc)
        if alerts:
            send_emergency_notification(alerts)
```
> The `watch_vitals_stream()` function in `backend/triggers.py` implements this exact pattern.
        """)

    # ── Threshold reference table ─────────────────────────────────────────────
    st.markdown("#### 📋 NICU Safe Threshold Ranges")
    threshold_data = [
        {"Vital Sign": k.replace("_", " ").title(),
         "Min": v["min"], "Max": v["max"], "Unit": v["unit"]}
        for k, v in THRESHOLDS.items()
    ]
    st.dataframe(pd.DataFrame(threshold_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 🚨 Live Alert Scan Results")
    st.caption("Replays the trigger logic over all existing vitals for this admission.")

    # ── Run threshold check ───────────────────────────────────────────────────
    alerts, trigger_sql = run_trigger_on_all_vitals(admission_id)

    if not alerts:
        st.success("✅ All recorded vitals are within normal NICU ranges.")
    else:
        # Group by severity
        critical = [a for a in alerts if a["severity"] == "CRITICAL"]
        warnings  = [a for a in alerts if a["severity"] == "WARNING"]

        if critical:
            st.error(f"🔴 {len(critical)} CRITICAL alert(s) detected!")
        if warnings:
            st.warning(f"🟡 {len(warnings)} WARNING alert(s) detected!")

        for alert in alerts:
            if alert["severity"] == "CRITICAL":
                st.error(alert["message"])
            else:
                st.warning(alert["message"])

        st.markdown("#### 📊 Alert Details")
        alert_df = pd.DataFrame(alerts)[
            ["label", "value", "unit", "direction", "severity", "threshold_min", "threshold_max", "record_time"]
        ]
        alert_df.columns = ["Vital", "Value", "Unit", "Direction", "Severity", "Min", "Max", "Recorded At"]
        st.dataframe(alert_df, use_container_width=True, hide_index=True)
