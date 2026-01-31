import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. IMPORT MODULAR RESEARCH FILES ---
# Ensure these files exist in your GitHub repository
try:
    from research_engine import log_temporal_trace, get_agentic_hint
    from admin_dashboard import show_admin_portal
    from database_manager import save_research_data
except ImportError as e:
    st.error(f"❌ Critical Error: Missing Research Modules. {e}")
    st.stop()

# --- 2. CONFIGURATION & SESSION STATE ---
st.set_page_config(page_title="AI-Chem Research Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. PAGE FUNCTIONS (DEFINED BEFORE USE) ---

def show_login():
    st.title("🇳🇵 PhD Research: AI in Chemistry")
    st.subheader("Login with your Research ID")
    input_id = st.text_input("Research ID:", placeholder="e.g. S001")
    if st.button("Enter Portal"):
        users_df = conn.read(worksheet="Participants")
        user_row = users_df[users_df['User_ID'] == input_id]
        if not user_row.empty:
            st.session_state.logged_in = True
            st.session_state.user_data = user_row.iloc[0].to_dict()
            log_temporal_trace("USER_LOGIN_SUCCESS")
            st.rerun()
        else:
            st.error("Access Denied: ID not found.")

def show_home():
    user = st.session_state.user_data
    st.header(f"Welcome, {user.get('Name', 'Participant')}")
    st.write(f"**Research Group:** {user.get('Group', 'Control')}")
    st.markdown("### 📜 Research Information\nThis study investigates AI scaffolding in Chemistry.")
    if st.sidebar.button("Logout"):
        log_temporal_trace("USER_LOGOUT")
        st.session_state.logged_in = False
        st.rerun()

# Import the new function at the top of main_app.py
from database_manager import save_temporal_traces

def show_quiz():
    # ... existing quiz code ...
    if submitted:
        # Save the actual quiz answers
        if save_response(data): 
            # NOW: Sync the temporal traces to Google Drive
            save_temporal_traces(conn, st.session_state.trace_buffer)
            st.success("Quiz and Temporal Traces synced to Google Drive!")
            
# --- 4. MAIN NAVIGATION ROUTING ---
if not st.session_state.logged_in:
    show_login()
else:
    user_info = st.session_state.user_data
    role = user_info.get('Role', 'Student')
    
    st.sidebar.title("🔬 Research Menu")
    pages = ["Home", "Quiz"]
    if role in ["Admin", "Supervisor"]:
        pages.append("Researcher Dashboard")
    
    choice = st.sidebar.selectbox("Go to:", pages)
    
    if choice == "Home": 
        show_home()
    elif choice == "Quiz": 
        show_quiz()
    elif choice == "Researcher Dashboard": 
        show_admin_portal(conn)
