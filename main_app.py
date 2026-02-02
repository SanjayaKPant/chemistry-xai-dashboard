import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import check_login, save_quiz_responses, save_temporal_traces
from research_engine import get_agentic_hint

# --- 1. CONFIGURATION & UI STYLING ---
st.set_page_config(page_title="Chem-XAI Research Lab", page_icon="🧪", layout="wide")

# Professional Research UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stRadio > label { font-size: 1.2rem; font-weight: bold; color: #1c3d5a; }
    .stAlert { border-radius: 10px; border-left: 8px solid #007bff; }
    .stButton > button { border-radius: 20px; background-color: #007bff; color: white; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []

# --- 2. TEMPORAL TRACE HELPER ---
def log_temporal_trace(event_type, details=""):
    user_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    trace = {
        "User_ID": user_id,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type,
        "Details": str(details)
    }
    st.session_state.trace_buffer.append(trace)

# --- 3. QUIZ INTERFACE ---
def show_quiz():
    user = st.session_state.user_data
    st.title("🧪 Atomic Structure Diagnostic")
    
    # Visual Progress Bar
    progress = 0
    if st.session_state.get('q1') != "Select...": progress += 25
    if st.session_state.get('q3'): progress += 25
    st.progress(progress / 50) # Simple 2-step progress visual
    
    st.info(f"Welcome, {user['Name']}! Let's explore the atom together.")
    
    # --- TIER 1 ---
    t1 = st.radio("1️⃣ Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # Agentic Scaffolding (XAI Hints)
    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.info(f"🤖 **AI Tutor:** {hint}")
                log_temporal_trace("HINT_VIEWED", details=t1)

    st.divider()

    # --- TIER 2: EMOJI SLIDER ---
    st.write("2️⃣ **How sure are you about that choice?**")
    t2_emoji = st.select_slider(
        "Slide the emoji to match your feeling:",
        options=["🤔 Not Sure", "🤨 Maybe", "🙂 Confident", "😎 Totally Sure!"],
        key="q2_ui"
    )

    # --- TIER 3 ---
    st.write("3️⃣ **Explain your scientific reasoning:**")
    t3 = st.text_area("Why did you choose that answer?", placeholder="Because...", key="q3")
    
    # --- TIER 4: EMOJI SLIDER ---
    st.write("4️⃣ **How sure are you about your explanation?**")
    t4_emoji = st.select_slider(
        "How confident is your reasoning?",
        options=["🤔 Not Sure", "🤨 Maybe", "🙂 Confident", "😎 Totally Sure!"],
        key="q4_ui"
    )

    # Mapping Emojis back to Research Data strings for your Admin Dashboard
    emoji_map = {
        "🤔 Not Sure": "Not Confident",
        "🤨 Maybe": "Somewhat",
        "🙂 Confident": "Confident",
        "😎 Totally Sure!": "Very Confident"
    }

    # --- SUBMIT BUTTON ---
    # Ensure this block is indented exactly once inside the show_quiz function
    if st.button("🚀 Finish & Submit Assessment", key="final_btn"):
        if t1 == "Select...":
            st.warning("Please answer Question 1 before submitting!")
        elif not t3.strip():
            st.warning("Please provide your reasoning in Tier 3.")
        else:
            quiz_data = {
                "User_ID": user['User_ID'],
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Tier_1": t1, 
                "Tier_2": emoji_map[t2_emoji], 
                "Tier_3": t3, 
                "Tier_4": emoji_map[t4_emoji]
            }
            if save_quiz_responses(quiz_data):
                save_temporal_traces(st.session_state.trace_buffer)
                st.success("✅ Research Data Synced! Great job!")
                st.balloons()
