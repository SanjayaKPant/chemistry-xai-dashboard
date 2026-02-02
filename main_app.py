import streamlit as st
import pandas as pd
from datetime import datetime
# Note: 'conn' is removed because gspread handles connection internally
from database_manager import check_login, save_quiz_responses, save_temporal_traces
from research_engine import get_agentic_hint

# --- 1. CONFIGURATION & SESSION STATE ---
st.set_page_config(page_title="AI-Chem Research Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []

# --- 2. TEMPORAL TRACE HELPER ---
# Moved here to ensure it has direct access to session_state
def log_temporal_trace(event_type, details=""):
    user_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    trace = {
        "User_ID": user_id,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type,
        "Details": str(details)
    }
    st.session_state.trace_buffer.append(trace)

# --- 3. QUIZ INTERFACE FUNCTION ---
def show_quiz():
    user = st.session_state.user_data
    st.title("🧪 Chemistry Diagnostic: Atomic Structure")
    
    # --- TIER 1 ---
    t1 = st.radio("Tier 1: Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1_v3")

    # --- AGENTIC SCAFFOLDING ---
    if t1 != "Select...":
        # Check experimental group status
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.info(f"🤖 **AI Tutor:** {hint}")
                log_temporal_trace("HINT_VIEWED", details=t1)

    st.divider()

    # --- TIERS 2, 3, 4 ---
    t2 = st.select_slider("Tier 2: How confident are you in this choice?", 
                          options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q2_v3")
    
    t3 = st.text_area("Tier 3: Scientific Reasoning (Explain your choice below):", key="q3_v3")
    
    t4 = st.select_slider("Tier 4: How confident are you in your explanation?", 
                          options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q4_v3")

    # --- SUBMIT BUTTON ---
    if st.button("Submit Research Data", key="final_btn"):
        if t1 == "Select...":
            st.warning("Please answer Tier 1.")
        else:
            quiz_data = {
                "User_ID": user['User_ID'],
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Tier_1": t1, 
                "Tier_2": t2, 
                "Tier_3": t3, 
                "Tier_4": t4
            }
            
            # Using the new robust gspread saving logic
            if save_quiz_responses(quiz_data):
                save_temporal_traces(st.session_state.trace_buffer)
                st.success("✅ Assessment & Temporal Traces Synced to Google Drive!")
                st.balloons()

# --- 4. NAVIGATION & ROUTING ---
if not st.session_state.logged_in:
    st.title("🔐 Researcher Login")
    u_id = st.text_input("Enter User ID (e.g., S001):").upper()
    if st.button("Login"):
        # This now triggers the gspread handshake in database_manager.py
        if check_login(u_id):
            log_temporal_trace("LOGIN_SUCCESS", details=u_id)
            st.rerun()
        else:
            # Error message is already handled inside check_login via st.error
            pass
else:
    with st.sidebar:
        st.write(f"👤 **User:** {st.session_state.user_data.get('Name', 'Unknown')}")
        st.write(f"📊 **Group:** {st.session_state.user_data.get('Group', 'Unknown')}")
        page = st.selectbox("Go to:", ["Quiz", "Research Dashboard"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.rerun()

    if page == "Quiz":
        show_quiz()
    else:
        # Import only when needed to prevent circular import issues
        try:
            from admin_dashboard import show_admin_portal
            show_admin_portal()
        except ImportError:
            st.error("Admin Dashboard module not found.")
