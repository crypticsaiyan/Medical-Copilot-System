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
from streamlit.errors import StreamlitAPIException

try:
    st.set_page_config(
        page_title="M28 — NICU Monitor",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except StreamlitAPIException:
    pass

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
    st.subheader("🗄️ Database Explorer — All Collections & Relations")
    st.caption("Browse every MongoDB collection from your ER diagram and the simulated Views (aggregation pipelines).")

    # ── 6 sub-tabs ──────────────────────────────────────────────────────
    (
        dbt1, dbt2, dbt3, dbt4, dbt5, dbt6
    ) = st.tabs([
        "Neonate",
        "NICU_ADMISSION",
        "Nurse_Observation",
        "Vital_Signs_Record",
        "Monitoring_Device",
        "Admitted_to (Relation)",
    ])

    # ─ 1. Neonate ────────────────────────────────────────────────
    with dbt1:
        st.caption("🏛️ **Entity:** `Neonate` | **PK:** `neonate_id`")
        try:
            from backend.admissions import get_all_neonates
            docs, raw_q = get_all_neonates()
            if docs:
                df = pd.DataFrame(docs).drop(columns=["_id"], errors="ignore")
                # Format date
                if "dob" in df.columns:
                    df["dob"] = pd.to_datetime(df["dob"]).dt.strftime("%Y-%m-%d")
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(df)} records")
            else:
                st.info("No records.")
        except Exception as e:
            st.error(str(e))

    # ─ 2. NICU_ADMISSION ──────────────────────────────────────────
    with dbt2:
        st.caption("🏛️ **Entity:** `NICU_ADMISSION` | **PK:** `admission_id` | **Relation:** `Admitted_to (Neonate)`")
        try:
            from backend.admissions import get_active_admissions
            docs, _ = get_active_admissions()
            if docs:
                df = pd.DataFrame(docs).drop(columns=["_id"], errors="ignore")
                if "admission_date" in df.columns:
                    df["admission_date"] = pd.to_datetime(df["admission_date"]).dt.strftime("%Y-%m-%d %H:%M")
                # Highlight FK column
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(df)} records | FK `neonate_id` references `neonates.neonate_id`")
            else:
                st.info("No records.")
        except Exception as e:
            st.error(str(e))

    # ─ 3. Nurse_Observation ──────────────────────────────────────
    with dbt3:
        st.caption("🏛️ **Entity:** `Nurse_Observation` | **PK:** `observation_id` | **Relation:** `Observed_in (NICU_ADMISSION)`")
        try:
            from backend.observations import get_all_observations
            docs, _ = get_all_observations()
            if docs:
                df = pd.DataFrame(docs).drop(columns=["_id"], errors="ignore")
                if "observation_time" in df.columns:
                    df["observation_time"] = pd.to_datetime(df["observation_time"]).dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(df)} records | FK `admission_id` references `nicu_admissions.admission_id`")
            else:
                st.info("No records.")
        except Exception as e:
            st.error(str(e))

    # ─ 4. Vital_Signs_Record ────────────────────────────────────
    with dbt4:
        st.caption("🏛️ **Entity:** `Vital_Signs_Record` | **PK:** `record_id` | **Relations:** `Monitored_by`, `Generated_by`")
        try:
            from backend.vitals import get_all_vitals
            docs, _ = get_all_vitals()
            if docs:
                df = pd.DataFrame(docs).drop(columns=["_id"], errors="ignore")
                if "record_time" in df.columns:
                    df["record_time"] = pd.to_datetime(df["record_time"]).dt.strftime("%Y-%m-%d %H:%M")
                df = df.sort_values("record_time", ascending=False).reset_index(drop=True) if "record_time" in df.columns else df
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(df)} records | FKs: `admission_id` → `nicu_admissions`, `device_id` → `monitoring_devices`")
            else:
                st.info("No records.")
        except Exception as e:
            st.error(str(e))

    # ─ 5. Monitoring_Device ──────────────────────────────────────
    with dbt5:
        st.caption("🏛️ **Entity:** `Monitoring_Device` | **PK:** `device_id` | **Relation:** `Generated_by`")
        try:
            docs, _ = get_all_devices()
            if docs:
                df = pd.DataFrame(docs).drop(columns=["_id"], errors="ignore")
                if "last_calibrated" in df.columns:
                    df["last_calibrated"] = pd.to_datetime(df["last_calibrated"]).dt.strftime("%Y-%m-%d")
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(df)} records")
            else:
                st.info("No records.")
        except Exception as e:
            st.error(str(e))

    # ─ 6. Admitted_to (Relation View) ──────────────
    with dbt6:
        st.caption("🔗 **Relation:** `Admitted_to` (simulated SQL JOIN between Neonate and NICU_ADMISSION)")
        st.code(
            "SELECT a.admission_id, n.name, n.gestational_age_weeks, n.birth_weight_g,\n"
            "       a.bed_no, a.diagnosis, a.status\n"
            "FROM nicu_admissions a\n"
            "LEFT JOIN neonates n ON a.neonate_id = n.neonate_id",
            language="sql",
        )
        try:
            rows, pipeline = neonate_admission_join_view()
            with st.expander("🔍 MongoDB Aggregation Pipeline", expanded=False):
                import json
                st.code(json.dumps(pipeline, indent=2, default=str), language="json")
            if rows:
                df = pd.DataFrame(rows)
                if "admission_date" in df.columns:
                    df["admission_date"] = pd.to_datetime(df["admission_date"]).dt.strftime("%Y-%m-%d")
                st.dataframe(df.drop(columns=["_id"], errors="ignore"),
                             use_container_width=True, hide_index=True)
                st.caption(f"{len(df)} joined records")
        except Exception as e:
            st.error(str(e))

