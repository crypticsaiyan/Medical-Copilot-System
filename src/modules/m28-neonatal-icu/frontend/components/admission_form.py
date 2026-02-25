"""
frontend/components/admission_form.py
──────────────────────────────────────
Form to register a new neonate and create their first NICU admission.
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime, timezone

from backend.admissions import add_neonate, admit_neonate
from frontend.components.query_display import show_raw_query

UTC = timezone.utc
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]
GENDERS      = ["Male", "Female", "Other"]


def render_admission_form() -> None:
    """Full-page form to admit a new neonate. Shows both insert queries on success."""
    st.subheader("🏥 Admit New Neonate")
    st.markdown("Complete all fields — both a Neonate record and an Admission record will be created.")

    with st.form("admission_form", clear_on_submit=True):
        st.markdown("**👶 Neonate Details**")
        col1, col2, col3 = st.columns(3)
        name        = col1.text_input("Full Name",        placeholder="e.g. Riya Patel")
        dob         = col2.date_input("Date of Birth",    value=datetime.now(UTC).date())
        gender      = col3.selectbox("Gender",            GENDERS)

        col4, col5, col6 = st.columns(3)
        blood_group = col4.selectbox("Blood Group",       BLOOD_GROUPS)
        ga_weeks    = col5.number_input("Gestational Age (weeks)", min_value=22, max_value=45, value=32)
        birth_wt    = col6.number_input("Birth Weight (g)",        min_value=300, max_value=5000, value=1500)

        st.markdown("**🛏️ Admission Details**")
        col7, col8, col9 = st.columns(3)
        bed_no    = col7.text_input("Bed No.", placeholder="e.g. B-05")
        diagnosis = col8.text_input("Diagnosis", placeholder="e.g. Neonatal Sepsis")

        submitted = st.form_submit_button("✅ Admit Neonate", use_container_width=True)

    if submitted:
        if not name or not bed_no or not diagnosis:
            st.error("Name, Bed No., and Diagnosis are required.")
            return

        dob_dt = datetime.combine(dob, datetime.min.time()).replace(tzinfo=UTC)

        # Insert neonate
        neonate_doc, neonate_query = add_neonate(
            name=name, dob=dob_dt, blood_group=blood_group,
            gestational_age_weeks=int(ga_weeks), gender=gender,
            birth_weight_g=float(birth_wt),
        )

        # Insert admission linked to the new neonate
        _, admission_query = admit_neonate(
            neonate_id=neonate_doc["neonate_id"],
            bed_no=bed_no,
            diagnosis=diagnosis,
        )

        st.success(f"✅ **{name}** admitted successfully! ID: `{neonate_doc['neonate_id']}`")
        col_a, col_b = st.columns(2)
        with col_a:
            show_raw_query(neonate_query,  "🔍 Insert: Neonate Document")
        with col_b:
            show_raw_query(admission_query,"🔍 Insert: Admission Document")
