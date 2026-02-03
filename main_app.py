import streamlit as st
import pandas as pd
import time
from datetime import datetime
from research_engine import get_agentic_hint
from database_manager import check_login, save_quiz_responses, save_temporal_traces, analyze_reasoning_quality

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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'trace_buffer' not in st.session_state: st.session_state.trace_buffer = []

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
            st.markdown(f'<div class="ai-chat-bubble">🤖 <b>AI Tutor:</b> I noticed your answer. Would you like a hint?</div>', unsafe_allow_html=True)
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                if st.button("💡 Socratic Clue"):
                    log_temporal_trace("HINT_SOCRATIC_CLICKED", details=t1)
                    st.info("🔍 Think about space: If the nucleus is a marble in a stadium, where are the electrons?")
            with col_h2:
                if col_h2.button("📖 Analogy"):
                    log_temporal_trace("HINT_ANALOGY_CLICKED", details=t1)
                    st.info("🐝 Imagine bees swarming so fast they look like a blurry cloud.")

        st.divider()
        t2 = st.select_slider("Step 2: Confidence", options=["Low", "Somewhat", "High", "Very High"], key="q2")
        t3 = st.text_area("Step 3: Why did you choose that?", key="q3")

        if t3.strip() and st.button("🚀 Submit Research Data"):
            score, keywords = analyze_reasoning_quality(t3)
            quiz_data = {
                "User_ID": user['User_ID'], "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "NLP_Score": score
            }
            if save_quiz_responses(quiz_data):
                save_temporal_traces(st.session_state.get('trace_buffer', []))
                st.success(f"✅ Data Synced! NLP Score: {score}")
                st.session_state.trace_buffer = []

# --- 5. ROUTING ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    u_id = st.text_input("ID:").upper().strip()
    if st.button("Login"):
        if check_login(u_id): st.rerun()
else:
    if st.session_state.user_data.get('Role') == 'Admin':
        from admin_dashboard import show_admin_portal
        show_admin_portal()
    else:
        show_quiz()
