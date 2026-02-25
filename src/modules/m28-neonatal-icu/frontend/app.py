"""
frontend/app.py
───────────────
Module 28 — Neonatal ICU Monitoring System
Main Streamlit entrypoint.

Run from the module root:
    streamlit run frontend/app.py

Tabs
────
  1. 🏥 Admissions     — register a new neonate, view active admissions table
  2. 📊 Vitals Monitor — time-series charts + aggregation summary
  3. 👩‍⚕️ Observations  — nurse observation log + new entry form
  4. ⚠️ Trigger Alerts — simulated AFTER INSERT trigger / Change Stream alerts
  5. 🗄️ DB Explorer    — daily admissions view, device list, raw collection browser
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Ensure module root is on sys.path ─────────────────────────────────────────
MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="M28 — NICU Monitoring System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Header gradient bar */
    .nicu-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
        padding: 1.2rem 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.2rem;
    }
    .nicu-header h1 { margin: 0; font-size: 1.8rem; }
    .nicu-header p  { margin: 0.2rem 0 0; opacity: 0.75; font-size: 0.9rem; }

    /* Softer expander styling */
    .streamlit-expanderHeader {
        background: #f0f4ff !important;
        border-radius: 6px !important;
    }
    /* Wider main content */
    .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Lazy imports (after sys.path fix) ─────────────────────────────────────────
from database.connection import ping, db, DB_NAME
from backend.admissions import get_all_neonates, get_active_admissions
from backend.analytics import daily_admissions_view, neonate_admission_join_view
from backend.devices import get_all_devices
from frontend.components.admission_form import render_admission_form
from frontend.components.patient_selector import render_patient_selector
from frontend.components.vitals_chart import render_vitals_chart
from frontend.components.observations_panel import render_observations_panel
from frontend.components.trigger_alerts import render_trigger_alerts
from frontend.components.query_display import show_raw_query

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nicu-header">
  <h1>🏥 Neonatal ICU Monitoring System</h1>
  <p>Module 28 · DBMS Project · MongoDB Atlas · Python + Streamlit</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar: connection status + quick stats ──────────────────────────────────
with st.sidebar:
    st.markdown("### 🗄️ Database Status")
    connected = ping()
    if connected:
        st.success(f"✅ Atlas Connected\n\n`{DB_NAME}`")
    else:
        st.error("❌ MongoDB Unreachable")
        st.stop()

    st.markdown("---")
    # Quick counts
    try:
        n_neonates   = db["neonates"].count_documents({})
        n_admissions = db["nicu_admissions"].count_documents({"status": "Admitted"})
        n_vitals     = db["vital_signs_records"].count_documents({})
        st.metric("Total Neonates",    n_neonates)
        st.metric("Active Admissions", n_admissions)
        st.metric("Vital Readings",    n_vitals)
    except Exception:
        pass

    st.markdown("---")
    st.markdown("#### ⚡ Quick Actions")
    if st.button("🔄 Re-seed Database", help="Clears and re-inserts all demo data"):
        from database.seed import seed
        with st.spinner("Seeding..."):
            seed()
        st.success("Database re-seeded!")
        st.rerun()

# ── Main tab layout ───────────────────────────────────────────────────────────
(
    tab_admit,
    tab_vitals,
    tab_obs,
    tab_trigger,
    tab_db,
) = st.tabs([
    "🏥 Admissions",
    "📊 Vitals Monitor",
    "👩‍⚕️ Nurse Observations",
    "⚠️ Trigger Alerts",
    "🗄️ DB Explorer",
])

# ─── Tab 1: Admissions ────────────────────────────────────────────────────────
with tab_admit:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        render_admission_form()

    with col_right:
        st.subheader("📋 Active Admissions (with $lookup join)")
        rows, pipeline = neonate_admission_join_view()
        show_raw_query(pipeline, "🔍 Aggregation Pipeline: Neonate–Admission JOIN")
        if rows:
            df = pd.DataFrame(rows)
            display_cols = [c for c in [
                "neonate_name", "bed_no", "diagnosis", "gestational_age_weeks",
                "birth_weight_g", "admission_id", "neonate_id",
            ] if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No active admissions.")

# ─── Tabs 2–4: need a patient selected ───────────────────────────────────────
with tab_vitals:
    admission_id_v, _ = render_patient_selector()
    if admission_id_v:
        st.markdown("---")
        render_vitals_chart(admission_id_v)

with tab_obs:
    admission_id_o, _ = render_patient_selector()
    if admission_id_o:
        st.markdown("---")
        render_observations_panel(admission_id_o)

with tab_trigger:
    admission_id_t, label_t = render_patient_selector()
    if admission_id_t:
        st.markdown("---")
        render_trigger_alerts(admission_id_t)

# ─── Tab 5: DB Explorer ───────────────────────────────────────────────────────
with tab_db:
    st.subheader("🗄️ Database Explorer")

    sub1, sub2 = st.tabs(["📅 Daily Admissions View", "🔧 Monitoring Devices"])

    with sub1:
        st.markdown("##### Aggregation Pipeline: Daily Admissions Count")
        st.caption("Simulates: `CREATE VIEW v_daily_admissions AS SELECT DATE(...), COUNT(*) FROM nicu_admissions GROUP BY DATE`")
        rows_d, pipeline_d = daily_admissions_view()
        show_raw_query(pipeline_d, "🔍 Aggregation Pipeline: Daily Admissions")
        if rows_d:
            df_d = pd.DataFrame(rows_d)
            st.dataframe(df_d, use_container_width=True, hide_index=True)
        else:
            st.info("No admission data available.")

    with sub2:
        st.markdown("##### Monitoring Devices")
        devices, raw_q = get_all_devices()
        show_raw_query(raw_q, "🔍 Query: All Monitoring Devices")
        if devices:
            df_dev = pd.DataFrame(devices)
            st.dataframe(df_dev.drop(columns=["_id"], errors="ignore"),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No devices found.")
