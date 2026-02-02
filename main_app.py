import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import check_login, save_quiz_responses, save_temporal_traces
from research_engine import get_agentic_hint

# --- 1. CONFIGURATION & DISTRACTION-FREE CSS ---
st.set_page_config(page_title="Chem-XAI Research Lab", page_icon="🧪", layout="wide")

st.markdown("""
    <style>
    /* Hide Streamlit Branding/Github for students */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #f0f2f6; }
    
    /* Chat-style AI Bubble */
    .chat-bubble {
        background-color: #e7f3ff;
        border-left: 5px solid #007bff;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0px;
        font-family: 'Helvetica';
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* 4-Block Confidence Styling */
    .conf-block {
        border: 2px solid #d1d5db;
        border-radius: 10px;
        padding: 10px;
        background-color: white;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Session State Initializations
for key in ['logged_in', 'user_data', 'trace_buffer', 'quiz_step']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'logged_in' else (None if key == 'user_data' else ([] if key == 'trace_buffer' else 1))

def log_temporal_trace(event_type, details=""):
    user_id = st.session_state.user_data.get('User_ID', 'Unknown') if st.session_state.user_data else "Unknown"
    st.session_state.trace_buffer.append({
        "User_ID": user_id, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type, "Details": str(details)
    })

# --- 2. THE IMPROVED STUDENT INTERFACE ---
def show_quiz():
    user = st.session_state.user_data
    st.title("🧪 Atomic Structure Journey")
    
    # Step 1: Content Question
    st.subheader("Part 1: Concept")
    t1 = st.radio("Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # Step 2: AI Tutor Chatbot Style
    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.markdown(f'''<div class="chat-bubble">🤖 <b>AI Tutor:</b> {hint}</div>''', unsafe_allow_html=True)
                log_temporal_trace("HINT_VIEWED", details=t1)

        st.divider()
        # Step 3: Confidence Grid (Rectangular Blocks)
        st.subheader("Part 2: Certainty")
        st.write("How sure are you about your choice?")
        t2 = st.select_slider("", options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q2")
        
        # Step 4: Reasoning & Final Confidence
        st.divider()
        st.subheader("Part 3: Reasoning")
        t3 = st.text_area("Explain your scientific reasoning:", placeholder="I think this because...", key="q3")
        
        if t3:
            st.subheader("Part 4: Final Reflection")
            t4 = st.select_slider("How confident is your explanation?", options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q4")

            if st.button("🚀 Submit Research Data"):
                quiz_data = {"User_ID": user['User_ID'], "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "Tier_4": t4}
                if save_quiz_responses(quiz_data):
                    save_temporal_traces(st.session_state.trace_buffer)
                    st.success("✅ Assessment Complete! Data Synced.")
                    st.balloons()

# --- 3. THE ADMIN INTERFACE ---
def show_admin():
    from admin_dashboard import show_admin_portal
    show_admin_portal()

# --- 4. NAVIGATION & ROLE ACCESS ---
if not st.session_state.logged_in:
    st.title("🔐 Research Portal Login")
    u_id = st.text_input("Enter ID:").upper().strip()
    if st.button("Login"):
        if check_login(u_id):
            log_temporal_trace("LOGIN_SUCCESS", details=u_id)
            st.rerun()
else:
    user = st.session_state.user_data
    role = user.get('Role', 'Student')
    
    with st.sidebar:
        st.header(f"👤 {user.get('Name')}")
        st.write(f"Role: {role}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Access Logic: Admins see Dashboard, Students see Quiz
    if role == 'Admin':
        show_admin()
    else:
        show_quiz()
