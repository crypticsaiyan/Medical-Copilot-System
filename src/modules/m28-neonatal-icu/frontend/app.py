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
    st.subheader("🗄️ Database Explorer — All Collections & Relations")
    st.caption("Browse every MongoDB collection from your ER diagram and the simulated Views (aggregation pipelines).")

    # ── 7 sub-tabs ──────────────────────────────────────────────────────
    (
        dbt1, dbt2, dbt3, dbt4, dbt5, dbt6, dbt7
    ) = st.tabs([
        "👶 Neonates",
        "🏥 NICU Admissions",
        "👩‍⚕️ Observations",
        "📊 Vital Signs",
        "🔧 Devices",
        "🔗 Neonate–Admission Join",
        "📅 Daily Admissions",
    ])

    # ─ 1. Neonates ────────────────────────────────────────────────
    with dbt1:
        st.caption("🏛️ **Collection:** `neonates` | **PK:** `neonate_id`")
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

    # ─ 2. NICU Admissions ──────────────────────────────────────────
    with dbt2:
        st.caption("🏛️ **Collection:** `nicu_admissions` | **PK:** `admission_id` | **FK:** `neonate_id → neonates`")
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

    # ─ 3. Nurse Observations ──────────────────────────────────────
    with dbt3:
        st.caption("🏛️ **Collection:** `nurse_observations` | **PK:** `observation_id` | **FK:** `admission_id → nicu_admissions`")
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

    # ─ 4. Vital Signs Records ────────────────────────────────────
    with dbt4:
        st.caption("🏛️ **Collection:** `vital_signs_records` | **PK:** `record_id` | **FK:** `admission_id`, `device_id`")
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

    # ─ 5. Monitoring Devices ──────────────────────────────────────
    with dbt5:
        st.caption("🏛️ **Collection:** `monitoring_devices` | **PK:** `device_id`")
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

    # ─ 6. Neonate–Admission Relationship (simulated SQL JOIN) ──────────────
    with dbt6:
        st.caption("🔗 **Simulates SQL JOIN:** `nicu_admissions LEFT JOIN neonates ON neonate_id` via `$lookup`")
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

    # ─ 7. Daily Admissions Aggregation (simulated View) ─────────────────
    with dbt7:
        st.caption("📅 **Simulates SQL View:** `GROUP BY DATE(admission_date)` via `$group`")
        st.code(
            "CREATE VIEW v_daily_admissions AS\n"
            "SELECT DATE(admission_date) AS day, COUNT(*) AS total\n"
            "FROM nicu_admissions GROUP BY DATE(admission_date)",
            language="sql",
        )
        try:
            rows_d, pipeline_d = daily_admissions_view()
            with st.expander("🔍 MongoDB Aggregation Pipeline", expanded=False):
                import json
                st.code(json.dumps(pipeline_d, indent=2, default=str), language="json")
            if rows_d:
                df_d = pd.DataFrame(rows_d)
                st.dataframe(df_d, use_container_width=True, hide_index=True)
                st.bar_chart(df_d.set_index(df_d.columns[0])[df_d.columns[1]] if len(df_d.columns) >= 2 else df_d)
        except Exception as e:
            st.error(str(e))
