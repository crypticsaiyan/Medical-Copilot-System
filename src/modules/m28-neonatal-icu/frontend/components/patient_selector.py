"""
frontend/components/patient_selector.py
Each tab passes a unique `tab_key` to avoid StreamlitDuplicateElementKey.
"""
from __future__ import annotations
import streamlit as st
from backend.analytics import neonate_admission_join_view


def render_patient_selector(tab_key: str = "default") -> tuple:
    """
    Display active-admissions selectbox.
    tab_key must be unique per tab (e.g. 'vitals', 'obs', 'trigger').
    """
    st.subheader("👶 Select Patient")
    try:
        rows, _ = neonate_admission_join_view()
    except Exception as e:
        st.error(f"Could not load admissions: {e}")
        return None, None

    if not rows:
        st.info("No active admissions found. Re-seed via sidebar.")
        return None, None

    options = {
        f"{r.get('neonate_name','?')} — Bed {r.get('bed_no')} [{r.get('admission_id')}]": r["admission_id"]
        for r in rows
    }

    selected_label = st.selectbox(
        "Active Admission",
        list(options.keys()),
        key=f"ps_{tab_key}",          # ← unique per tab
    )
    selected_id = options[selected_label]

    sel = next((r for r in rows if r["admission_id"] == selected_id), None)
    if sel:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🛏️ Bed",          sel.get("bed_no", "—"))
        c2.metric("⚖️ Birth Wt",     f"{sel.get('birth_weight_g', '—')} g")
        c3.metric("🗓️ GA Weeks",     sel.get("gestational_age_weeks", "—"))
        c4.metric("🔬 Diagnosis",    sel.get("diagnosis", "—"))

    return selected_id, selected_label
