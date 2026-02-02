import streamlit as st
import pandas as pd
import time
from datetime import datetime
from database_manager import check_login, save_quiz_responses, save_temporal_traces
from research_engine import get_agentic_hint

# --- 1. CONFIGURATION & UI STYLING ---
st.set_page_config(page_title="Chem-XAI Lab", page_icon="🧪", layout="wide")

# Inject CSS for Chat-Style AI Tutor and Distraction-Free UI
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .ai-chat-bubble {
        background-color: #f0f7ff;
        border-radius: 20px;
        padding: 20px;
        border: 2px solid #007bff;
        margin-bottom: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE GUARDRAILS ---
# Ensuring variables exist before any logic runs to prevent AttributeError
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

def log_temporal_trace(event_type, details=""):
    """Saves user interaction timestamps for Process Mining."""
    if 'trace_buffer' not in st.session_state:
        st.session_state.trace_buffer = []
    
    user_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    st.session_state.trace_buffer.append({
        "User_ID": user_id, 
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type, 
        "Details": str(details)
    })

# --- 3. THE STUDENT EXPERIENCE (GRID + TIMER) ---
def show_quiz():
    user = st.session_state.user_data
    st.title("⚛️ Atomic Structure Journey")
    
    # Grid Part 1: Concept Question
    with st.container():
        st.subheader("Step 1: The Atomic Concept")
        t1 = st.radio("Where are electrons primarily located?", 
                      ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # AI Tutor Chat Scaffolding
    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.markdown(f'<div class="ai-chat-bubble"><b>🤖 AI Tutor:</b> {hint}</div>', unsafe_allow_html=True)

        st.divider()
        # Grid Part 2: Choice Certainty and Reasoning
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Step 2: Certainty")
            t2 = st.select_slider("How sure are you about Part 1?", 
                                 options=["Not Confident", "Somewhat", "Confident", "Very Confident"], 
                                 key="q2")
        with col2:
            st.markdown("### Step 3: Reasoning")
            t3 = st.text_area("Why did you choose that answer?", placeholder="Because...", key="q3")

        # Grid Part 4: Submission with Timer logic
        if t3.strip():
            st.divider()
            st.subheader("Step 4: Final Confidence")
            t4 = st.select_slider("How confident is your scientific reasoning?", 
                                 options=["Not Confident", "Somewhat", "Confident", "Very Confident"], 
                                 key="q4")

            if st.button("🚀 Finalize & Submit Research Data"):
                total_duration = round(time.time() - st.session_state.start_time, 2)
                
                quiz_data = {
                    "User_ID": user['User_ID'], 
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "Tier_4": t4
                }
                
                # Submission Guard: Ensures trace_buffer exists
                current_traces = st.session_state.get('trace_buffer', [])
                
                try:
                    with st.spinner("Syncing data to Google Cloud..."):
                        if save_quiz_responses(quiz_data):
                            save_temporal_traces(current_traces)
                            st.success(f"✅ Data synced! Time taken: {total_duration}s")
                            st.balloons()
                            # Reset for next run
                            st.session_state.trace_buffer = []
                            st.session_state.start_time = time.time()
                except Exception as e:
                    st.error(f"Error during submission: {e}")

# --- 4. NAVIGATION ROUTER ---
if not st.session_state.logged_in:
    st.title("🧪 Chem-XAI Research Login")
    u_id = st.text_input("Enter Participant ID:").upper().strip()
    if st.button("Login"):
        if check_login(u_id):
            st.session_state.start_time = time.time() # Start timer on login
            st.rerun()
else:
    user = st.session_state.user_data
    # Access Control: Only 'Admin' sees Dashboard
    if user.get('Role') == 'Admin':
        from admin_dashboard import show_admin_portal
        show_admin_portal()
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        # Student View
        with st.sidebar:
            st.header(f"👤 {user.get('Name')}")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()
        show_quiz()
