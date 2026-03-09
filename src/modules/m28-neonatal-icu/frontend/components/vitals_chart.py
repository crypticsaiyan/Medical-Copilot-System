"""
frontend/components/vitals_chart.py
Multi-chart vitals dashboard for a selected admission.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from backend.vitals import get_vitals_for_admission
from backend.analytics import vital_signs_summary_view, alert_vitals_view

NORMAL_RANGES = {
    "heart_rate":       (100, 160, "bpm"),
    "spo2":             (94,  100, "%"),
    "respiratory_rate": (30,  60,  "/min"),
    "temp":             (36.5,37.5,"°C"),
    "systolic_bp":      (45,  80,  "mmHg"),
    "diastolic_bp":     (25,  55,  "mmHg"),
}


def render_vitals_chart(admission_id: str) -> None:
    vitals, _ = get_vitals_for_admission(admission_id)
    if not vitals:
        st.info("No vitals recorded for this admission yet.")
        return

    df = pd.DataFrame(vitals)
    df["record_time"] = pd.to_datetime(df["record_time"], utc=True)
    df = df.sort_values("record_time").reset_index(drop=True)

    # ── Latest values row ────────────────────────────────────────────────────
    latest = df.iloc[-1]
    st.markdown("#### 🔢 Latest Readings")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    def _delta(col, lo, hi):
        v = latest.get(col, None)
        if v is None: return "—", None
        ok = lo <= v <= hi
        return f"{v}", "normal" if ok else "inverse"
    for (col, label, (lo,hi,unit)), cell in zip(
        [("heart_rate","❤️ HR",NORMAL_RANGES["heart_rate"]),
         ("spo2","🫁 SpO2",NORMAL_RANGES["spo2"]),
         ("respiratory_rate","🌬️ RR",NORMAL_RANGES["respiratory_rate"]),
         ("temp","🌡️ Temp",NORMAL_RANGES["temp"]),
         ("systolic_bp","🩸 SBP",NORMAL_RANGES["systolic_bp"]),
         ("diastolic_bp","🩸 DBP",NORMAL_RANGES["diastolic_bp"])],
        [c1,c2,c3,c4,c5,c6]
    ):
        val, delta_color = _delta(col, lo, hi)
        cell.metric(f"{label} ({unit})", val, delta_color=delta_color if delta_color else "normal")

    st.markdown("---")

    # ── Tab charts ────────────────────────────────────────────────────────────
    ct1, ct2, ct3, ct4 = st.tabs(["❤️ Heart & O₂", "🌬️ Breathing & Temp", "🩸 Blood Pressure", "📊 Summary Stats"])

    with ct1:
        cols_hr = ["record_time","heart_rate","spo2"]
        valid = [c for c in cols_hr if c in df.columns]
        if len(valid) > 1:
            chart_df = df[valid].set_index("record_time")
            chart_df.columns = ["Heart Rate (bpm)", "SpO2 (%)"]
            st.line_chart(chart_df)
            # Alert band annotations (text)
            lo_hr, hi_hr, _ = NORMAL_RANGES["heart_rate"]
            alerts_hr = df[(df["heart_rate"] < lo_hr) | (df["heart_rate"] > hi_hr)]
            if not alerts_hr.empty:
                st.warning(f"⚠️ {len(alerts_hr)} heart rate reading(s) outside {lo_hr}–{hi_hr} bpm")

    with ct2:
        cols_br = ["record_time","respiratory_rate","temp"]
        valid = [c for c in cols_br if c in df.columns]
        if len(valid) > 1:
            chart_df = df[valid].set_index("record_time")
            chart_df.columns = ["Respiratory Rate (/min)", "Temperature (°C)"]
            st.line_chart(chart_df)
            lo_rr, hi_rr, _ = NORMAL_RANGES["respiratory_rate"]
            alerts_rr = df[(df["respiratory_rate"] < lo_rr) | (df["respiratory_rate"] > hi_rr)]
            if not alerts_rr.empty:
                st.warning(f"⚠️ {len(alerts_rr)} respiratory rate reading(s) outside {lo_rr}–{hi_rr} /min")

    with ct3:
        bp_cols = ["record_time","systolic_bp","diastolic_bp"]
        has_bp = all(c in df.columns for c in bp_cols)
        if has_bp:
            bp_df = df[bp_cols].set_index("record_time")
            bp_df.columns = ["Systolic BP (mmHg)", "Diastolic BP (mmHg)"]
            st.area_chart(bp_df)
        else:
            st.info("No BP data available for this admission.")

    with ct4:
        # Aggregation summary
        summary, _ = vital_signs_summary_view(admission_id)
        if summary:
            s = summary[0]
            agg_data = {
                "Metric": ["Heart Rate","SpO2","Resp Rate"],
                "Min":  [s.get("min_heart_rate","—"), s.get("min_spo2","—"), "—"],
                "Max":  [s.get("max_heart_rate","—"), "100", "—"],
                "Avg":  [round(s.get("avg_heart_rate",0),1), round(s.get("avg_spo2",0),1), round(s.get("avg_respiratory_rate",0),1)],
            }
            st.dataframe(pd.DataFrame(agg_data), use_container_width=True, hide_index=True)

        # Alert count bar chart
        alerts, _ = alert_vitals_view(admission_id)
        if alerts:
            st.markdown(f"##### ⚠️ {len(alerts)} Out-of-Range Readings")
            alert_df = pd.DataFrame(alerts)
            if "record_time" in alert_df.columns:
                alert_df["record_time"] = pd.to_datetime(alert_df["record_time"]).dt.strftime("%H:%M")
            st.dataframe(alert_df[["record_time","heart_rate","spo2","respiratory_rate","temp"]].rename(columns={
                "record_time":"Time","heart_rate":"HR","spo2":"SpO2","respiratory_rate":"RR","temp":"Temp"
            }), use_container_width=True, hide_index=True)
        else:
            st.success("✅ All readings within normal range.")

    # ── Raw data expander (collapsed) ─────────────────────────────────────────
    with st.expander("📋 Raw Vitals Data", expanded=False):
        show_df = df.copy()
        show_df["record_time"] = show_df["record_time"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(show_df.drop(columns=["_id","record_id","admission_id","device_id"], errors="ignore"),
                     use_container_width=True, hide_index=True)
