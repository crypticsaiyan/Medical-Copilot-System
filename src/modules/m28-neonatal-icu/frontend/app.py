"""
frontend/app.py — Module 28: Neonatal ICU Monitoring System
Run from project root:
    streamlit run src/modules/m28-neonatal-icu/frontend/app.py
"""
from __future__ import annotations

# ── sys.path fix (must be FIRST) ──────────────────────────────────────────────
import sys
from pathlib import Path
_MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE_ROOT))
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="M28 — NICU Monitor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.nicu-header{background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:white;
  padding:1.2rem 1.8rem;border-radius:12px;margin-bottom:1rem}
.nicu-header h1{margin:0;font-size:1.8rem}
.nicu-header p{margin:.2rem 0 0;opacity:.75;font-size:.9rem}
.block-container{padding-top:1rem!important}
</style>""", unsafe_allow_html=True)

# ── Lazy local imports (after path fix) ───────────────────────────────────────
from database.connection import ping, db, DB_NAME
from backend.admissions import get_all_neonates
from backend.analytics import daily_admissions_view, neonate_admission_join_view
from backend.devices import get_all_devices
from frontend.components.admission_form import render_admission_form
from frontend.components.patient_selector import render_patient_selector
from frontend.components.vitals_chart import render_vitals_chart
from frontend.components.observations_panel import render_observations_panel
from frontend.components.trigger_alerts import render_trigger_alerts

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""<div class="nicu-header">
  <h1>🏥 Neonatal ICU Monitoring System</h1>
  <p>Module 28 · DBMS Project · MongoDB Atlas · Python + Streamlit</p>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗄️ Database Status")
    connected = ping()
    if connected:
        st.success(f"✅ Atlas Connected\n\n`{DB_NAME}`")
    else:
        st.error("❌ MongoDB Unreachable")
        st.stop()

    st.markdown("---")
    # Always-fresh counts (reads directly from DB, no cache)
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
    if st.button("🔄 Re-seed Database", help="Clears and re-inserts all demo data"):
        from database.seed import seed
        with st.spinner("Seeding..."):
            seed(drop_existing=True)
        st.success("Database re-seeded!")
        st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_admit, tab_vitals, tab_obs, tab_trigger, tab_db = st.tabs([
    "🏥 Admissions",
    "📊 Vitals Monitor",
    "👩‍⚕️ Nurse Observations",
    "⚠️ Trigger Alerts",
    "🗄️ DB Explorer",
])

# Tab 1 — Admissions
with tab_admit:
    col_left, col_right = st.columns([1, 1], gap="large")
    with col_left:
        render_admission_form()
    with col_right:
        st.subheader("📋 Active Admissions")
        try:
            rows, _ = neonate_admission_join_view()
            if rows:
                df = pd.DataFrame(rows)
                display_cols = [c for c in [
                    "neonate_name","bed_no","diagnosis",
                    "gestational_age_weeks","birth_weight_g","admission_id",
                ] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No active admissions.")
        except Exception as e:
            st.error(str(e))

# Tab 2 — Vitals
with tab_vitals:
    admission_id_v, _ = render_patient_selector(tab_key="vitals")
    if admission_id_v:
        st.markdown("---")
        render_vitals_chart(admission_id_v)

# Tab 3 — Observations
with tab_obs:
    admission_id_o, _ = render_patient_selector(tab_key="obs")
    if admission_id_o:
        st.markdown("---")
        render_observations_panel(admission_id_o)

# Tab 4 — Trigger Alerts
with tab_trigger:
    admission_id_t, _ = render_patient_selector(tab_key="trigger")
    if admission_id_t:
        st.markdown("---")
        render_trigger_alerts(admission_id_t)

# Tab 5 — DB Explorer
with tab_db:
    st.subheader("🗄️ Database Explorer")
    sub1, sub2 = st.tabs(["📅 Daily Admissions View", "🔧 Monitoring Devices"])

    with sub1:
        st.caption("Simulates: `CREATE VIEW v_daily_admissions AS SELECT DATE(admission_date), COUNT(*) FROM nicu_admissions GROUP BY DATE`")
        try:
            rows_d, pipeline_d = daily_admissions_view()
            with st.expander("🔍 Show Aggregation Pipeline", expanded=False):
                import json
                st.code(json.dumps(pipeline_d, indent=2, default=str), language="json")
            if rows_d:
                st.dataframe(pd.DataFrame(rows_d), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(str(e))

    with sub2:
        st.markdown("##### Monitoring Devices")
        try:
            devices, _ = get_all_devices()
            if devices:
                df_dev = pd.DataFrame(devices)
                st.dataframe(df_dev.drop(columns=["_id"], errors="ignore"),
                             use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(str(e))
