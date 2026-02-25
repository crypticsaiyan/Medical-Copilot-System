"""
frontend/components/query_display.py
─────────────────────────────────────
Reusable component that renders a MongoDB query / pipeline
inside a styled st.expander — satisfying the "show raw DB mechanics" requirement.
"""
from __future__ import annotations

import json
import streamlit as st


def show_raw_query(query: dict | list, title: str = "🔍 Raw MongoDB Query") -> None:
    """Render a query dict or aggregation pipeline list inside an expander."""
    with st.expander(title, expanded=False):
        if isinstance(query, list):
            st.caption("Aggregation Pipeline")
            for i, stage in enumerate(query):
                st.markdown(f"**Stage {i + 1}**")
                st.code(json.dumps(stage, indent=2, default=str), language="json")
        else:
            st.caption("Query / Operation")
            st.code(json.dumps(query, indent=2, default=str), language="json")
