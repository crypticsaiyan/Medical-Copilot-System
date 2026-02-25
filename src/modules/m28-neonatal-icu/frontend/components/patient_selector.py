"""
frontend/components/patient_selector.py
────────────────────────────────────────
Renders a selectbox that lets the user choose an active admission.
Returns the selected (admission_id, neonate_name) pair.
"""
from __future__ import annotations

import streamlit as st
from backend.admissions import get_active_admissions
from backend.analytics import neonate_admission_join_view
from frontend.components.query_display import show_raw_query


def render_patient_selector() -> tuple[str | None, str | None]:
    """
    Display an active-admissions dropdown.
    Returns (admission_id, display_label) or (None, None) if no data.
    """
    st.subheader("👶 Select Patient")

    rows, pipeline = neonate_admission_join_view()
    show_raw_query(pipeline, "🔍 Query: Active Admissions ($lookup join)")

    if not rows:
        st.info("No active admissions found. Seed the database first.")
        return None, None

    options = {
        f"{r.get('neonate_name', 'Unknown')} — Bed {r.get('bed_no')} [{r.get('admission_id')}]": r["admission_id"]
        for r in rows
    }

    selected_label = st.selectbox("Active Admission", list(options.keys()), key="patient_selector")
    selected_admission_id = options[selected_label]

    # Show a summary card for the selected patient
    selected = next((r for r in rows if r["admission_id"] == selected_admission_id), None)
    if selected:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛏️ Bed",        selected.get("bed_no", "—"))
        col2.metric("⚖️ Birth Weight", f"{selected.get('birth_weight_g', '—')} g")
        col3.metric("🗓️ GA Weeks",    selected.get("gestational_age_weeks", "—"))
        col4.metric("🔬 Diagnosis",   selected.get("diagnosis", "—"))

    return selected_admission_id, selected_label
