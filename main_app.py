import streamlit as st
import pandas as pd
from database_manager import check_login, log_temporal_trace

# --- 1. MANDATORY SESSION INITIALIZATION ---
if 'gate' not in st.session_state: st.session_state.gate = None
if 'user' not in st.session_state: st.session_state.user = None
if 'target_group' not in st.session_state: st.session_state.target_group = "Exp_A"

st.set_page_config(page_title="Chemistry PhD Portal", layout="wide")

# --- 2. MODULAR IMPORTS ---
try:
    import student_portal
    import teacher_portal
    import researcher_portal
except ImportError as e:
    st.error(f"Missing Module: {e}")

# --- 3. GATEWAY LOGIC ---
if st.session_state.user is None:
    st.title("🎓 Chemistry PhD Research Portal")
    choice = st.sidebar.selectbox("Select Gate", ["Student Gate", "Teacher Gate", "Researcher Gate"])
    
    # Simulating a login for your debug session
    if st.sidebar.button("Login"):
        # Replace this with your actual database_manager.check_login logic
        st.session_state.user = {"id": "S001", "name": "Test User", "group": "Exp_A"}
        st.session_state.gate = choice
        st.rerun()
else:
    # --- 4. PORTAL ROUTING ---
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    if st.session_state.gate == "Student Gate":
        student_portal.show()
    elif st.session_state.gate == "Teacher Gate":
        teacher_portal.show()
    elif st.session_state.gate == "Researcher Gate":
        researcher_portal.show()
