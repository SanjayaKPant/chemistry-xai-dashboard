import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Triadic AI-Chem Portal", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.trace_buffer = [] # For Temporal Analytics (Theme 9)

# --- HIGH-FIDELITY TEMPORAL LOGGER ---
def log_trace(event_type, details=""):
    """Captures timestamps for Educational Process Mining (Gašević-style)."""
    if st.session_state.user_data:
        trace = {
            "User_ID": st.session_state.user_data.get('User_ID'),
            "Timestamp": datetime.now().isoformat(),
            "Event": event_type,
            "Details": details
        }
        st.session_state.trace_buffer.append(trace)

# --- UPDATED AUTHENTICATION ---
def authenticate_user(user_id):
    try:
        # ttl=0 ensures we always get the latest student list from GSheets
        users_df = conn.read(worksheet="Participants", ttl=0)
        user_row = users_df[users_df['User_ID'] == user_id]
        if not user_row.empty:
            return user_row.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Auth System Error: {e}")
        return None

# --- RE-ENGINEERED LOGIN PAGE ---
def show_login():
    st.title("🇳🇵 PhD Research: AI in Chemistry")
    st.subheader("Login with your Research ID")
    
    with st.container(border=True):
        input_id = st.text_input("Research ID:", placeholder="e.g. S001")
        if st.button("Enter Portal"):
            user_info = authenticate_user(input_id)
            if user_info:
                st.session_state.logged_in = True
                st.session_state.user_data = user_info
                log_trace("USER_LOGIN_SUCCESS")
                st.rerun()
            else:
                st.error("Access Denied: ID not found in the research database.")

# --- NAVIGATION & PAGES ---
if not st.session_state.logged_in:
    show_login()
else:
    user = st.session_state.user_data
    st.sidebar.title("🔬 Research Menu")
    st.sidebar.write(f"Logged in as: **{user['Name']}**")
    
    # Consistent use of variables to prevent KeyErrors
    role = user.get('Role', 'Student')
    group = user.get('Group', 'Control')
    
    choice = st.sidebar.selectbox("Go to:", ["Home", "4-Tier Quiz"])
    
    if choice == "Home":
        st.header(f"Welcome, {user['Name']}")
        st.write(f"Research Group: **{group}**")
        if st.sidebar.button("Logout"):
            log_trace("USER_LOGOUT")
            st.session_state.logged_in = False
            st.rerun()
            
    elif choice == "4-Tier Quiz":
        st.header("📝 Diagnostic Assessment")
        with st.form("quiz_form"):
            t1 = st.radio("Where are electrons located?", ["Nucleus", "Electron Cloud"])
            t2 = st.slider("Confidence:", 0, 100)
            t3 = st.text_area("Reasoning (Tier 3):")
            
            if st.form_submit_button("Submit Response"):
                log_trace("QUIZ_SUBMISSION_ATTEMPT")
                # Add your save_response logic here
                if group == "Exp_C" and t1 == "Nucleus":
                    st.warning("🤖 Agentic Hint: Recall Rutherford's experiment. What is actually in the center?")
                    log_trace("SCAFFOLD_DISPLAYED", details="Nucleus Misconception")
