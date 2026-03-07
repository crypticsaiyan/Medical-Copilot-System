"""
frontend/components/patient_selector.py
────────────────────────────────────────
Renders a selectbox that lets the user choose an active admission.
Returns the selected (admission_id, neonate_name) pair.

Each call site passes a unique `tab_key` so Streamlit doesn't
raise StreamlitDuplicateElementKey when used in multiple tabs.
"""
from __future__ import annotations

import streamlit as st
from backend.analytics import neonate_admission_join_view
from frontend.components.query_display import show_raw_query


def render_patient_selector(tab_key: str = "default") -> tuple[str | None, str | None]:
    """
    Display an active-admissions dropdown.

    Parameters
    ----------
    tab_key : str
        Unique suffix for the Streamlit widget key — must differ across tabs.

    Returns
    -------
    (admission_id, display_label) or (None, None) if no data.
    """
    st.subheader("👶 Select Patient")

    try:
        rows, pipeline = neonate_admission_join_view()
    except Exception as e:
        st.error(f"Could not load admissions: {e}")
        return None, None

    show_raw_query(pipeline, "🔍 Query: Active Admissions ($lookup join)")

    if not rows:
        st.info("No active admissions found. Use the sidebar to re-seed the database.")
        return None, None

    options = {
        f"{r.get('neonate_name', 'Unknown')} — Bed {r.get('bed_no')} [{r.get('admission_id')}]": r["admission_id"]
        for r in rows
    }

    # Each tab passes a unique tab_key to avoid duplicate widget keys
    selected_label = st.selectbox(
        "Active Admission",
        list(options.keys()),
        key=f"patient_selector_{tab_key}",
    )
    selected_admission_id = options[selected_label]

    # Summary metrics card
    selected = next((r for r in rows if r["admission_id"] == selected_admission_id), None)
    if selected:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛏️ Bed",          selected.get("bed_no", "—"))
        col2.metric("⚖️ Birth Weight",  f"{selected.get('birth_weight_g', '—')} g")
        col3.metric("🗓️ GA Weeks",      selected.get("gestational_age_weeks", "—"))
        col4.metric("🔬 Diagnosis",     selected.get("diagnosis", "—"))

    return selected_admission_id, selected_label
