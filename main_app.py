"""
main_app.py — MMALE Research Portal Entry Point
=================================================
Routing logic: login → role-based portal dispatch.

Changes from original:
  - Added admin_dashboard import for Admin/Supervisor role
  - Added agent_completed session state initialisation
  - All other logic preserved exactly as original
"""

import streamlit as st
import database_manager as db

st.set_page_config(
    page_title="Chemistry AI-X | MMALE Research Portal",
    page_icon="🧪",
    layout="wide",
)

import student_portal
import teacher_portal
import researcher_portal
import admin_dashboard

# ── Session state defaults ────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# Ensure multi-agent state keys exist from session start
if "agent_completed" not in st.session_state:
    st.session_state.agent_completed = {}
if "current_tap_level" not in st.session_state:
    st.session_state.current_tap_level = "TAP_1"
if "current_rep_level" not in st.session_state:
    st.session_state.current_rep_level = "MONADIC"

# ── Login screen ──────────────────────────────────────────────────────────────
if st.session_state.user is None:
    st.title("🧪 Chemistry AI-X Research Portal")
    st.markdown(
        "### Multimodal Multi-Agent Learning Ecology (MMALE)\n"
        "Evidence-Based Socratic Learning | नेपाली र अंग्रेजी"
    )

    col1, _ = st.columns([1, 1])
    with col1:
        user_id = st.text_input(
            "Enter User ID (e.g. STD_1001, T101, R001)"
        ).strip().upper()

    if st.button("Login | लगइन"):
        user_data = db.check_login(user_id)
        if user_data:
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("❌ ID not found. Please verify with the Participants database.")

# ── Authenticated routing ─────────────────────────────────────────────────────
else:
    st.sidebar.title(f"👤 {st.session_state.user.get('Name')}")
    role = str(st.session_state.user.get("Role", "Student")).strip()
    st.sidebar.write(f"**Role:** {role}")
    st.sidebar.write(f"**Group:** {st.session_state.user.get('Group', '—')}")

    if st.sidebar.button("Logout | बाहिरिनुहोस्"):
        st.session_state.clear()
        st.rerun()

    # PhD routing logic
    if role in ["Admin"]:
        admin_dashboard.show_admin_portal()
    elif role in ["Researcher", "Supervisor"]:
        researcher_portal.show()
    elif role in ["Teacher", "Head Teacher"]:
        teacher_portal.show()
    else:
        student_portal.show()
