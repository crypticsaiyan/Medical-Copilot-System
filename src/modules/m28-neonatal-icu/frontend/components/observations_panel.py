"""
frontend/components/observations_panel.py
──────────────────────────────────────────
Renders nurse observation records for a selected admission,
plus the log-new-observation form.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from backend.observations import (
    get_observations_for_admission,
    log_observation,
)
from frontend.components.query_display import show_raw_query

UTC = timezone.utc

FEEDING_OPTIONS  = ["Breastfed", "Formula", "IV Nutrition", "NPO", "Mixed"]
CRYING_OPTIONS   = ["None", "Mild", "Moderate", "High"]


def render_observations_panel(admission_id: str) -> None:
    """Show all nurse observations and a form to log a new one."""
    st.subheader("👩‍⚕️ Nurse Observations")

    # ── Historical observations ───────────────────────────────────────────────
    records, raw_query = get_observations_for_admission(admission_id)
    show_raw_query(raw_query, "🔍 Query: Fetch Nurse Observations")

    if records:
        df = pd.DataFrame(records)
        df["observation_time"] = pd.to_datetime(df["observation_time"]).dt.strftime("%Y-%m-%d %H:%M")
        display_cols = [c for c in ["observation_id", "observation_time", "feeding_status", "crying_level", "notes"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
    else:
        st.info("No observations recorded yet.")

    st.markdown("---")

    # ── Log new observation form ──────────────────────────────────────────────
    st.markdown("#### ➕ Log New Observation")
    with st.form("new_observation_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        feeding = col1.selectbox("Feeding Status", FEEDING_OPTIONS)
        crying  = col2.selectbox("Crying Level",   CRYING_OPTIONS)
        notes   = st.text_area("Clinical Notes", placeholder="e.g. Mild subcostal recession, responding to CPAP...")
        submitted = st.form_submit_button("💾 Save Observation")

    if submitted:
        _, insert_query = log_observation(
            admission_id   = admission_id,
            feeding_status = feeding,
            crying_level   = crying,
            notes          = notes,
        )
        st.success("✅ Observation saved successfully!")
        show_raw_query(insert_query, "🔍 Query: Insert Nurse Observation")
        st.rerun()
