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

# --- 3. NAVIGATION LOGIC ---
if not st.session_state.logged_in:
    show_login() 
else:
    user = st.session_state.user_data
    role = user.get('Role', 'Student')
    
    # 2026 Modular Navigation Hub
    st.sidebar.title("🔬 Research Menu")
    st.sidebar.write(f"Logged in: **{user.get('Name')}**")
    
    pages = ["Home", "Course", "Quiz"]
    if role in ["Admin", "Supervisor"]:
        pages.append("Researcher Dashboard")
        
    choice = st.sidebar.selectbox("Navigation", pages)
    
    # --- PAGE ROUTING ---
    if choice == "Researcher Dashboard":
        show_admin_portal(conn)
    elif choice == "Home":
        show_home() # Ensure this function is still in main_app.py
    elif choice == "Quiz":
        show_quiz() # This is where we will trigger the research_engine
