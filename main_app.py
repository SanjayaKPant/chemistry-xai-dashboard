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
    st.info(f"Welcome, {user['Name']}! Please answer carefully. AI Tutor hints may appear to guide you.")
    
    # Tier 1
    t1 = st.radio("Tier 1: Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # Agentic Scaffolding Logic
    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.info(f"🤖 **AI Tutor:** {hint}")
                log_temporal_trace("HINT_VIEWED", details=t1)

    st.divider()
 # --- ENHANCED CONFIDENCE SLIDERS ---

# Tier 2: Confidence in Choice
st.subheader("How sure are you about your answer?")
t2_emoji = st.select_slider(
    "Slide to match your confidence level:",
    options=["🤔 Not Sure", "🤨 Maybe", "🙂 Confident", "😎 Totally Sure!"],
    key="q2_enhanced"
)

# ... inside the submit logic, you can map these back to your data values if needed
confidence_map = {
    "🤔 Not Sure": "Not Confident",
    "🤨 Maybe": "Somewhat",
    "🙂 Confident": "Confident",
    "😎 Totally Sure!": "Very Confident"
}
final_t2 = confidence_map[t2_emoji]
    t3 = st.text_area("Tier 3: Scientific Reasoning:", key="q3")
    t4 = st.select_slider("Tier 4: Confidence in explanation?", options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q4")

    if st.button("Submit Assessment", key="final_btn"):
        if t1 == "Select...":
            st.warning("Please answer Tier 1.")
        else:
            quiz_data = {
                "User_ID": user['User_ID'],
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "Tier_4": t4
            }
            if save_quiz_responses(quiz_data):
                save_temporal_traces(st.session_state.trace_buffer)
                st.success("✅ Research Data Synced!")
                st.balloons()

# --- 4. NAVIGATION ROUTING ---
if not st.session_state.logged_in:
    st.title("🔐 Researcher Login")
    u_id = st.text_input("User ID:").upper()
    if st.button("Login"):
        if check_login(u_id):
            log_temporal_trace("LOGIN_SUCCESS", details=u_id)
            st.rerun()
else:
    with st.sidebar:
        st.header(f"👤 {st.session_state.user_data['Name']}")
        st.write(f"Group: {st.session_state.user_data['Group']}")
        page = st.selectbox("Navigation", ["Quiz", "Research Dashboard"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if page == "Quiz":
        show_quiz()
    else:
        from admin_dashboard import show_admin_portal
        show_admin_portal()
