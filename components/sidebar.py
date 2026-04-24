# components/sidebar.py
import streamlit as st
from streamlit_option_menu import option_menu

def _menu_icons(length):
    base_icons = [
        "house",
        "activity",
        "flask",
        "capsule",
        "building",
        "credit-card",
        "people",
        "shield",
        "truck",
        "bar-chart",
    ]
    if length <= len(base_icons):
        return base_icons[:length]
    return (base_icons + ["circle"] * length)[:length]


def sidebar(menu_items, state_key="sidebar_selection", widget_key="sidebar_option_menu"):
    current_selection = st.session_state.get(state_key, menu_items[0])
    if current_selection not in menu_items:
        current_selection = menu_items[0]

    with st.sidebar:
        st.markdown("## 🏥 MediCare")
        selected = option_menu(
            "",
            menu_items,
            icons=_menu_icons(len(menu_items)),
            default_index=menu_items.index(current_selection),
            key=widget_key,
        )
        st.session_state[state_key] = selected

        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.session_state.role = None
            st.session_state.view = "main"
            st.session_state.selected_category = None
            st.session_state.selected_module = None
            st.rerun()

    return selected