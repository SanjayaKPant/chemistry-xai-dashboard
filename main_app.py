import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# At the top of main_app.py
try:
    from research_engine import log_temporal_trace, get_agentic_hint
    from admin_dashboard import show_admin_portal
    from database_manager import save_temporal_traces, save_quiz_responses
except ImportError as e:
    st.error(f"❌ Critical Error: Missing Research Modules. {e}")
    st.stop()

# --- 2. CONFIGURATION & SESSION STATE ---
st.set_page_config(page_title="AI-Chem Research Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. PAGE FUNCTIONS (DEFINED BEFORE USE) ---

def show_login():
    st.title("🇳🇵 PhD Research: AI in Chemistry")
    st.subheader("Login with your Research ID")
    input_id = st.text_input("Research ID:", placeholder="e.g. S001")
    if st.button("Enter Portal"):
        users_df = conn.read(worksheet="Participants")
        user_row = users_df[users_df['User_ID'] == input_id]
        if not user_row.empty:
            st.session_state.logged_in = True
            st.session_state.user_data = user_row.iloc[0].to_dict()
            log_temporal_trace("USER_LOGIN_SUCCESS")
            st.rerun()
        else:
            st.error("Access Denied: ID not found.")

def show_home():
    user = st.session_state.user_data
    st.header(f"Welcome, {user.get('Name', 'Participant')}")
    st.write(f"**Research Group:** {user.get('Group', 'Control')}")
    st.markdown("### 📜 Research Information\nThis study investigates AI scaffolding in Chemistry.")
    if st.sidebar.button("Logout"):
        log_temporal_trace("USER_LOGOUT")
        st.session_state.logged_in = False
        st.rerun()

# Import the new function at the top of main_app.py
from database_manager import save_temporal_traces

def show_quiz():
    st.title("🧪 Chemistry Diagnostic: Atomic Structure")
    
    # 1. Tier 1: Initial Choice
    t1 = st.radio("Tier 1: Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1")

    # 2. THE AGENTIC HINT (Appears immediately after T1)
    if t1 != "Select...":
        # We check both Group and a bypass for your test user S001
        user_id = st.session_state.user_data.get('User_ID')
        group = st.session_state.user_data.get('Group')
        
        if group == "Exp_A" or user_id == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.info(f"🤖 **Socratic Hint:** {hint}")
                log_temporal_trace("HINT_VIEWED", details=t1)

    st.divider()

    # 3. Tier 2 & 3: Confidence and Reasoning
    t2 = st.select_slider("Tier 2: How confident are you?", 
                          options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q2")
    
    t3 = st.text_area("Tier 3: Explain your reasoning (Reflecting on the hint if any):", key="q3")
    
    # 4. Tier 4: Meta-Confidence
    t4 = st.select_slider("Tier 4: Confidence in Reasoning?", 
                          options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q4")

    st.write("") # Spacer

    # 5. THE ONLY SUBMIT BUTTON (At the very bottom)
    if st.button("Submit Final Research Data"):
        if t1 == "Select...":
            st.error("Please select an answer for Tier 1.")
        else:
            quiz_results = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "User_ID": st.session_state.user_data['User_ID'],
                "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "Tier_4": t4
            }
            # Save to GSheets
            if save_quiz_responses(conn, quiz_results):
                save_temporal_traces(conn, st.session_state.trace_buffer)
                st.success("✅ Assessment and Traces successfully synced to Drive!")
                st.balloons()
                
    # 2. Final Reasoning
    t3 = st.text_area("Reflecting on the hint (if any), explain your final choice:")
    
    if st.button("Submit Final Answer"):
        # ... your existing save logic ...
        st.success("Data Captured!")

    # Now 'submitted' is defined and safe to check
    if submitted:
        log_temporal_trace("QUIZ_SUBMITTED", details=t1) # Capture specific tiers
        
        # Prepare data for Google Sheets
        quiz_data = {
            "Timestamp": datetime.now().isoformat(),
            "User_ID": user['User_ID'],
            "Tier_1": t1,
            "Tier_3": t3
        }
        
        # Use the modular database manager to save
        if save_quiz_responses(conn, quiz_data):
            save_temporal_traces(conn, st.session_state.trace_buffer)
            st.success("✅ Research data synced successfully!")
        else:
            st.error("❌ Sync failed. Please contact the researcher.")
            
# --- 4. MAIN NAVIGATION ROUTING ---
if not st.session_state.logged_in:
    show_login()
else:
    user_info = st.session_state.user_data
    role = user_info.get('Role', 'Student')
    
    st.sidebar.title("🔬 Research Menu")
    pages = ["Home", "Quiz"]
    if role in ["Admin", "Supervisor"]:
        pages.append("Researcher Dashboard")
    
    choice = st.sidebar.selectbox("Go to:", pages)
    
    if choice == "Home": 
        show_home()
    elif choice == "Quiz": 
        show_quiz()
    elif choice == "Researcher Dashboard": 
        show_admin_portal(conn)
