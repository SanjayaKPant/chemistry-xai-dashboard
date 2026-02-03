import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. SAFE IMPORTS ---
try:
    from database_manager import check_login, save_quiz_responses, save_temporal_traces, analyze_reasoning_quality
except ImportError:
    # Fallback: if the NLP function isn't in your database_manager yet, the app won't crash
    from database_manager import check_login, save_quiz_responses, save_temporal_traces
    def analyze_reasoning_quality(text): return 0, "none"

from research_engine import get_agentic_hint

# --- 2. PAGE CONFIG ---
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
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'user_data' not in st.session_state: 
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state: 
    st.session_state.trace_buffer = []
if 'start_time' not in st.session_state: 
    st.session_state.start_time = time.time()

def log_temporal_trace(event_type, details=""):
    if 'trace_buffer' not in st.session_state: 
        st.session_state.trace_buffer = []
    u_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    st.session_state.trace_buffer.append({
        "User_ID": u_id, 
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type, 
        "Details": str(details)
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
                    st.info("🔍 **Think about space:** If an atom was a stadium, and the nucleus was a marble, where would the electrons be?")
            with h_col2:
                if st.button("📖 See an Analogy"):
                    log_temporal_trace("HINT_ANALOGY_CLICKED", details=t1)
                    st.info("🐝 **The Beehive Model:** Imagine bees swarming so fast they look like a blurry cloud. Are they inside the hive
