"""
frontend/components/vitals_chart.py
─────────────────────────────────────
Renders interactive vital-signs time-series charts and
the aggregation summary table for a selected admission.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from backend.analytics import vital_signs_summary_view
from backend.vitals import get_vitals_for_admission
from frontend.components.query_display import show_raw_query


def render_vitals_chart(admission_id: str) -> None:
    """Display vitals time-series chart + summary stats for an admission."""
    st.subheader("📈 Vital Signs Monitor")

    # ── Raw readings ──────────────────────────────────────────────────────────
    records, raw_query = get_vitals_for_admission(admission_id)
    show_raw_query(raw_query, "🔍 Query: Fetch Vital Signs Records")

    if not records:
        st.info("No vital sign records found for this admission.")
        return

    df = pd.DataFrame(records)
    df["record_time"] = pd.to_datetime(df["record_time"])
    df = df.sort_values("record_time")

    # ── Metric summary row ────────────────────────────────────────────────────
    latest = df.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("❤️ Heart Rate",     f"{latest.get('heart_rate', '—')} bpm")
    c2.metric("🫁 SpO₂",           f"{latest.get('spo2', '—')} %")
    c3.metric("🌡️ Temperature",    f"{latest.get('temp', '—')} °C")
    c4.metric("💨 Resp. Rate",      f"{latest.get('respiratory_rate', '—')} /min")

    # ── Time-series charts ────────────────────────────────────────────────────
    chart_cols_map = {
        "Heart Rate (bpm)":     "heart_rate",
        "SpO₂ (%)":             "spo2",
        "Temperature (°C)":     "temp",
        "Respiratory Rate":     "respiratory_rate",
    }

    tab_names = list(chart_cols_map.keys())
    tabs = st.tabs(tab_names)
    for tab, (label, col) in zip(tabs, chart_cols_map.items()):
        with tab:
            if col in df.columns:
                chart_df = df.set_index("record_time")[[col]].rename(columns={col: label})
                st.line_chart(chart_df)
            else:
                st.caption(f"No data for {label}")

    # ── Aggregation View: summary stats ───────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 Aggregation View — Statistics Summary")
    st.caption("This aggregation pipeline simulates a SQL `CREATE VIEW` for average/min/max per admission.")

    summary, pipeline = vital_signs_summary_view(admission_id)
    show_raw_query(pipeline, "🔍 Aggregation Pipeline: Vital Signs Summary View")

    if summary:
        summary_df = pd.DataFrame(summary)
        summary_df.columns = [c.replace("_", " ").title() for c in summary_df.columns]
        st.dataframe(summary_df, use_container_width=True)

    # ── Full raw data table ───────────────────────────────────────────────────
    with st.expander("📋 Raw Vital Signs Data Table"):
        display_df = df.drop(columns=["_id"], errors="ignore")
        display_df["record_time"] = display_df["record_time"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(display_df, use_container_width=True)
