import streamlit as st
from streamlit_gsheets import GSheetsConnection
from research_engine import log_temporal_trace
from admin_dashboard import show_admin_portal

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
