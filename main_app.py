import streamlit as st
from streamlit_gsheets import GSheetsConnection
from research_engine import log_temporal_trace, get_agentic_hint # Ensure these are at the top
from admin_dashboard import show_admin_portal
from database_manager import save_research_data

# --- 1. SESSION STATE INITIALIZATION (MUST BE FIRST) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []

# --- 2. CONFIGURATION & CONNECTION ---
st.set_page_config(page_title="AI-Chem Research Portal", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. NAVIGATION LOGIC (Now safe to check) ---
if not st.session_state.logged_in:
    show_login() # Assuming show_login is defined in this file
else:
    user = st.session_state.user_data
    # ... rest of your navigation logic

# ... (Initialize Connection and Authentication logic)

if st.session_state.logged_in:
    user = st.session_state.user_data
    role = user.get('Role', 'Student')
    
    # 2026 Modular Navigation
    pages = ["Home", "Course", "Quiz"]
    if role in ["Admin", "Supervisor"]:
        pages.append("Researcher Dashboard")
        
    choice = st.sidebar.selectbox("Navigation", pages)
    
    if choice == "Researcher Dashboard":
        show_admin_portal(conn)
    # ... (Other Page Routes)
