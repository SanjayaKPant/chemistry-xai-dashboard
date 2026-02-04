import streamlit as st
# This MUST match the function names in your database_manager.py
from database_manager import (
    check_login, 
    save_quiz_responses, 
    save_temporal_traces, 
    analyze_reasoning_quality
)

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI for Science Lab", layout="wide")

# --- SESSION STATE INITIALIZATION ---
# This acts as the "memory" of your app
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# --- VIEW LOGIC ---
if not st.session_state.logged_in:
    # 1. LOGIN SCREEN
    st.title("🔐 PhD Research Portal: Login")
    st.write("Please enter your participant ID to access the Chemistry-XAI Dashboard.")
    
    user_input = st.text_input("Participant ID (e.g., S001)").strip().upper()
    
    if st.button("Access Dashboard"):
        if check_login(user_input):
            st.session_state.logged_in = True
            st.session_state.user_id = user_input
            st.rerun()  # Forces the app to refresh and show the Dashboard view
        else:
            st.error("Access Denied: ID not found in the research database.")

else:
    # 2. DASHBOARD VIEW (Shown only after successful login)
    st.sidebar.success(f"Logged in as: {st.session_state.user_id}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()

    st.title("🧪 Chemistry-XAI Research Dashboard")
    st.info(f"Welcome, Participant {st.session_state.user_id}. The system is ready.")
    
    # This is where your actual experiment content goes
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current Task")
        st.write("Analyze the molecular structures provided and submit your reasoning.")
    
    with col2:
        status = analyze_reasoning_quality([]) # Calling your stub function
        st.metric("System Status", status)
