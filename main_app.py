import streamlit as st
import pandas as pd
import time
from datetime import datetime
# Import our database and NLP tools
from database_manager import (
    check_login, 
    save_quiz_responses, 
    save_temporal_traces, 
    analyze_reasoning_quality  # Ensure this is in database_manager.py
)
from research_engine import get_agentic_hint

# --- 1. CONFIGURATION & DISTRACTION-FREE UI ---
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

# --- 2. SESSION STATE STABILITY ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'trace_buffer' not in st.session_state: st.session_state.trace_buffer = []
if 'start_time' not in st.session_state: st.session_state.start_time = time.time()

def log_temporal_trace(event_type, details=""):
    if 'trace_buffer' not in st.session_state: st.session_state.trace_buffer = []
    user_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    st.session_state.trace_buffer.append({
        "User_ID": user_id, 
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type, "Details": str(details)
    })

# --- 3. THE 4-BLOCK STUDENT INTERFACE ---
def show_quiz():
    user = st.session_state.user_data
    st.title("⚛️ Atomic Structure Journey")
    
    # BLOCK 1: Concept Question
    with st.container():
        st.subheader("Step 1: The Atomic Concept")
        t1 = st.radio("Where are electrons primarily located?", 
                      ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # BLOCK 2: High-Impact Adaptive Scaffolding
    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            st.markdown(f'<div class="ai-chat-bubble">🤖 <b>AI Tutor:</b> I noticed your answer, {user.get("Name")}. Would you like to explore a hint before writing your reasoning?</div>', unsafe_allow_html=True)
            
            h_col1, h_col2 = st.columns(2)
            with h_col1:
                if st.button("💡 Get a Socratic Clue"):
                    log_temporal_trace("HINT_SOCRATIC_CLICKED", details=t1)
                    st.info("🔍 **Think about space:** If an atom was the size of a football stadium, and the nucleus was a marble in the center, where would the electrons be?")
            
            with h_col2:
                if st.button("📖 See an Analogy"):
                    log_temporal_trace("HINT_ANALOGY_CLICKED", details=t1)
                    st.info("🐝 **The Beehive Model:** Imagine bees swarming around a hive. They move so fast they look like a blurry cloud. Are they inside the hive, or in the space around it?")

        st.divider()
        # BLOCK 3: Grid for Certainty and Reasoning
        col_cert, col_reas = st.columns(2)
        with col_cert:
            st.markdown("### Step 2: Certainty")
            t2 = st.select_slider("How sure are you about Part 1?", 
                                 options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q2")
        with col_reas:
            st.markdown("### Step 3: Reasoning")
            t3 = st.text_area("Why did you choose that answer?", placeholder="Explain your thinking...", key="q3")
