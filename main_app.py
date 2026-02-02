import streamlit as st
import pandas as pd
from datetime import datetime
# Import our robust database functions
from database_manager import check_login, save_quiz_responses, save_temporal_traces
from research_engine import get_agentic_hint

# --- 1. CONFIGURATION & PROFESSIONAL UI ---
st.set_page_config(
    page_title="Chem-XAI Research Lab", 
    page_icon="🧪", 
    layout="wide"
)

# Custom CSS for a modern, high-school friendly look
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .stRadio > label { font-size: 1.3rem; font-weight: bold; color: #1c3d5a; }
    .stAlert { border-radius: 12px; border-left: 10px solid #007bff; }
    .stButton > button { 
        border-radius: 25px; 
        background-color: #007bff; 
        color: white; 
        font-weight: bold;
        height: 3em;
        transition: 0.3s;
    }
    .stButton > button:hover { background-color: #0056b3; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session States
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []

# --- 2. RESEARCH UTILITIES ---
def log_temporal_trace(event_type, details=""):
    """Logs student interactions for Process Mining analysis."""
    user_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    trace = {
        "User_ID": user_id,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type,
        "Details": str(details)
    }
    st.session_state.trace_buffer.append(trace)

# --- 3. THE STUDENT QUIZ INTERFACE ---
def show_quiz():
    user = st.session_state.user_data
    st.title("🧪 Atomic Structure Diagnostic")
    
    # Progress bar: Helps high schoolers see the finish line
    progress = 0
    if st.session_state.get('q1') != "Select...": progress += 33
    if st.session_state.get('q3'): progress += 33
    st.progress(min(progress, 100))
    
    st.info(f"👋 Hello {user['Name']}! Let's test your knowledge of atoms.")
    
    # TIER 1: The Content Question
    t1 = st.radio("1️⃣ Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # XAI Agentic Scaffolding (Hints for Experimental Group)
    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.info(f"🤖 **AI Tutor:** {hint}")
                log_temporal_trace("HINT_VIEWED", details=t1)

    st.divider()

    # TIER 2: Emoji Confidence Slider
    st.write("2️⃣ **How sure are you about your answer?**")
    t2_emoji = st.select_slider(
        "Slide the emoji to match your feeling:",
        options=["🤔 Not Sure", "🤨 Maybe", "🙂 Confident", "😎 Totally Sure!"],
        key="q2_ui"
    )

    # TIER 3: Reasoning
    st.write("3️⃣ **Explain your scientific reasoning:**")
    t3 = st.text_area("Why did you choose that answer?", placeholder="Explain your thinking here...", key="q3")
    
    # TIER 4: Emoji Confidence Slider
    st.write("4️⃣ **How sure are you about your explanation?**")
    t4_emoji = st.select_slider(
        "How confident is your reasoning?",
        options=["🤔 Not Sure", "🤨 Maybe", "🙂 Confident", "😎 Totally Sure!"],
        key="q4_ui"
    )

    # Map Emojis to formal research data strings
    emoji_map = {
        "🤔 Not Sure": "Not Confident",
        "🤨 Maybe": "Somewhat",
        "🙂 Confident": "Confident",
        "😎 Totally Sure!": "Very Confident"
    }

    # SUBMIT LOGIC
    if st.button("🚀 Finish & Submit Assessment", key="final_btn"):
        if t1 == "Select...":
            st.warning("Please answer Question 1.")
        elif not t3.strip():
            st.warning("Please provide your reasoning for Tier 3.")
        else:
            quiz_data = {
                "User_ID": user['User_ID'],
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Tier_1": t1, 
                "Tier_2": emoji_map[t2_emoji], 
                "Tier_3": t3, 
                "Tier_4": emoji_map[t4_emoji]
            }
            with st.spinner("Saving to research database..."):
                if save_quiz_responses(quiz_data):
                    save_temporal_traces(st.session_state.trace_buffer)
                    st.success("✅ Research Data Synced! Thank you for participating.")
                    st.balloons()

# --- 4. LOGIN & NAVIGATION ROUTING ---
if not st.session_state.logged_in:
    st.title("🔐 Researcher Access Portal")
    st.write("Please log in with the ID provided by your instructor.")
    u_id = st.text_input("Enter User ID:").upper().strip()
    
    if st.button("Log In"):
        if u_id:
            # check_login uses cached gspread client for speed
            if check_login(u_id):
                log_temporal_trace("LOGIN_SUCCESS", details=u_id)
                st.rerun()
            else:
                st.error("Invalid User ID. Please try again.")
else:
    # Authenticated Sidebar
    with st.sidebar:
        st.header(f"👤 {st.session_state.user_data.get('Name', 'User')}")
        st.write(f"**Group:** {st.session_state.user_data.get('Group', 'N/A')}")
        st.divider()
        page = st.selectbox("Navigation", ["Quiz", "Research Dashboard"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.rerun()

    # Route to selected page
    if page == "Quiz":
        show_quiz()
    else:
        # Load heavy dashboard only when requested to save homepage speed
        try:
            from admin_dashboard import show_admin_portal
            show_admin_portal()
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")
