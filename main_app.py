import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import check_login, save_quiz_responses, save_temporal_traces
from research_engine import get_agentic_hint

# --- 1. RESEARCHER-ONLY CSS & DISTRACTION REMOVAL ---
st.set_page_config(page_title="Chem-XAI Lab", page_icon="🧪", layout="wide")

st.markdown("""
    <style>
    /* Hide GitHub, Menu, and Header for students */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chatbot Style Scaffolding */
    .ai-chat-bubble {
        background-color: #f0f7ff;
        border-radius: 20px;
        padding: 20px;
        border: 2px solid #007bff;
        margin-bottom: 20px;
    }
    
    /* Confidence Block Styling */
    .stSelectSlider { margin-bottom: 0px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE STUDENT EXPERIENCE (GRID LAYOUT) ---
def show_quiz():
    user = st.session_state.user_data
    st.title("⚛️ Atomic Structure Journey")
    
    # --- ROW 1: THE CONCEPT ---
    with st.container():
        st.subheader("Step 1: The Atomic Concept")
        t1 = st.radio("Where are electrons primarily located?", 
                      ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # --- ROW 2: AI TUTOR CHAT (Only for Exp Group) ---
    if t1 != "Select...":
        if user.get('Group') == "Exp_A" or user.get('User_ID') == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.markdown(f'<div class="ai-chat-bubble"><b>🤖 AI Tutor:</b> {hint}</div>', unsafe_allow_html=True)

        # --- ROW 3: THE CONFIDENCE GRID (Side-by-Side Blocks) ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Step 2: Choice Certainty")
            t2 = st.select_slider("How sure are you about Part 1?", 
                                 options=["Not Confident", "Somewhat", "Confident", "Very Confident"], 
                                 key="q2")
        
        with col2:
            st.markdown("### Step 3: Reasoning")
            t3 = st.text_area("Why did you choose that answer?", placeholder="Because...", key="q3")

        # --- ROW 4: FINAL REFLECTION ---
        if t3.strip():
            st.divider()
            st.subheader("Step 4: Explanation Confidence")
            t4 = st.select_slider("How confident is your scientific reasoning?", 
                                 options=["Not Confident", "Somewhat", "Confident", "Very Confident"], 
                                 key="q4")

            if st.button("🚀 Finalize & Submit Research Data"):
                quiz_data = {"User_ID": user['User_ID'], "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "Tier_4": t4}
                if save_quiz_responses(quiz_data):
                    save_temporal_traces(st.session_state.trace_buffer)
                    st.success("✅ Research data synced successfully!")
                    st.balloons()

# --- 3. THE ROLE-BASED ROUTER ---
if not st.session_state.get('logged_in'):
    st.title("🧪 Chem-XAI Research Login")
    u_id = st.text_input("Enter Participant ID:").upper().strip()
    if st.button("Login"):
        if check_login(u_id):
            st.rerun()
else:
    user = st.session_state.user_data
    # Determine if user is Admin or Student
    is_admin = user.get('Role') == 'Admin'
    
    with st.sidebar:
        st.header(f"👤 {user.get('Name')}")
        if is_admin:
            st.success("Admin Mode Active")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Lead Researcher sees Dashboard; Students see Quiz
    if is_admin:
        from admin_dashboard import show_admin_portal
        show_admin_portal()
    else:
        show_quiz()
