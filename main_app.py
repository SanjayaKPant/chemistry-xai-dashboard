import streamlit as st
import pandas as pd
import time
from datetime import datetime
from research_engine import get_agentic_hint

# --- 1. ROBUST IMPORTS ---
try:
    from database_manager import check_login, save_quiz_responses, save_temporal_traces, analyze_reasoning_quality
except ImportError:
    from database_manager import check_login, save_quiz_responses, save_temporal_traces
    def analyze_reasoning_quality(text): return 0, "none"

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="Chem-XAI Research Lab", page_icon="🧪", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .ai-chat-bubble {
        background-color: #e7f3ff;
        border-radius: 15px;
        padding: 15px;
        border-left: 5px solid #007bff;
        margin: 15px 0px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'trace_buffer' not in st.session_state: st.session_state.trace_buffer = []
if 'start_time' not in st.session_state: st.session_state.start_time = time.time()

def log_temporal_trace(event_type, details=""):
    if 'trace_buffer' not in st.session_state: st.session_state.trace_buffer = []
    u_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    st.session_state.trace_buffer.append({
        "User_ID": u_id, 
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type, "Details": str(details)
    })

# --- 4. STUDENT INTERFACE ---
def show_quiz():
    user = st.session_state.user_data
    st.title("⚛️ Atomic Structure Journey")
    st.subheader("Step 1: The Atomic Concept")
    
    t1 = st.radio("Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            name = user.get("Name", "Student")
            st.markdown(f'<div class="ai-chat-bubble">🤖 <b>AI Tutor:</b> I noticed your answer, {name}. Would you like to explore a hint?</div>', unsafe_allow_html=True)
            
            h_col1, h_col2 = st.columns(2)
            with h_col1:
                if st.button("💡 Get a Socratic Clue"):
                    log_temporal_trace("HINT_SOCRATIC_CLICKED", details=t1)
                    st.info("🔍 **Think about space:** If an atom was a stadium and the nucleus was a marble, where would the electrons be?")
            with h_col2:
                if st.button("📖 See an Analogy"):
                    log_temporal_trace("HINT_ANALOGY_CLICKED", details=t1)
                    st.info("🐝 **The Beehive Model:** Imagine bees swarming so fast they look like a blurry cloud. Are they inside the hive or in the space around it?")

        st.divider()
        col_cert, col_reas = st.columns(2)
        with col_cert:
            st.markdown("### Step 2: Certainty")
            t2 = st.select_slider("Confidence in Answer", options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q2")
        with col_reas:
            st.markdown("### Step 3: Reasoning")
            t3 = st.text_area("Why did you choose that answer?", placeholder="Explain your thinking...", key="q3")

        if t3.strip():
            st.divider()
            st.subheader("Step 4: Explanation Confidence")
            t4 = st.select_slider("Confidence in Reasoning", options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q4")

            if st.button("🚀 Finalize & Submit Research Data"):
                duration = round(time.time() - st.session_state.start_time, 2)
                score, keywords = analyze_reasoning_quality(t3)
                quiz_data = {
                    "User_ID": user['User_ID'], "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "Tier_4": t4,
                    "NLP_Score": score, "Keywords": keywords, "Total_Time": duration
                }
                if save_quiz_responses(quiz_data):
                    save_temporal_traces(st.session_state.get('trace_buffer', []))
                    st.success(f"✅ Synced! Score: {score}/7")
                    st.balloons()
                    st.session_state.trace_buffer = []

# --- 5. ROUTING ---
if not st.session_state.logged_in:
    st.title("🔐 Research Portal Login")
    u_id = st.text_input("Enter ID:").upper().strip()
    if st.button("Login"):
        if check_login(u_id):
            st.session_state.start_time = time.time()
            st.rerun()
else:
    user = st.session_state.user_data
    if user.get('Role') == 'Admin':
        from admin_dashboard import show_admin_portal
        show_admin_portal()
    else:
        with st.sidebar:
            st.header(f"👤 {user.get('Name')}")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()
        show_quiz()
