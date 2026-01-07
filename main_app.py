import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="AI-Chem Research Portal", layout="wide")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_group' not in st.session_state:
    st.session_state.user_group = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# --- MOCK MASTER LIST (In future, pull this from a 'Users' tab in your GSheet) ---
# Roles: 'Admin', 'Supervisor', 'Teacher', 'Student'
# Groups: 'Control', 'Exp_A', 'Exp_B', 'Exp_C'
USER_DB = {
    "ADMIN01": {"role": "Admin", "group": "All", "name": "Lead Researcher"},
    "SUP01": {"role": "Supervisor", "group": "All", "name": "Prof. Supervisor A"},
    "T001": {"role": "Teacher", "group": "Control", "name": "Science Teacher 1"},
    "S001": {"role": "Student", "group": "Exp_C", "name": "Student Alpha"}
}

# --- HELPER FUNCTIONS ---
def save_response(data_dict):
    """Saves 4-tier quiz data to Google Sheets"""
    try:
        existing_data = conn.read(worksheet="Responses")
        new_row = pd.DataFrame([data_dict])
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        conn.update(worksheet="Responses", data=updated_df)
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

# --- PAGE: LOGIN ---
def show_login():
    st.title("🇳🇵 AI-Integration in Chemistry Research")
    st.subheader("Participant Access Portal")
    
    with st.container(border=True):
        user_id = st.text_input("Enter your Unique Research ID:")
        if st.button("Access Dashboard"):
            if user_id in USER_DB:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_role = USER_DB[user_id]['role']
                st.session_state.user_group = USER_DB[user_id]['group']
                st.rerun()
            else:
                st.error("ID not found. Please contact the researcher.")

# --- PAGE: HOME (Welcome & Ethics) ---
def show_home():
    st.header(f"Welcome, {USER_DB[st.session_state.user_id]['name']}")
    st.write(f"**Group:** {st.session_state.user_group} | **Role:** {st.session_state.user_role}")
    
    st.markdown("""
    ### Research Overview
    This PhD study explores the impact of AI-integrated scaffolding on understanding **Chemical Bonding**.
    
    **Instructions:**
    1. Complete the assigned lessons in order.
    2. Answer all 4-tier diagnostic questions honestly.
    3. Do not refresh the page during a quiz.
    """)
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- PAGE: AI-INTEGRATED COURSE ---
def show_course():
    st.header("📚 Atomic Structure & Bonding")
    
    tabs = st.tabs(["L1: Atoms", "L2: Ions", "L3: Covalent", "L4: Lewis", "L5: Properties"])
    
    with tabs[0]:
        st.subheader("Lesson 1: Atomic Foundations")
        st.write("Atoms are the building blocks of matter...")
        # Add educational content here
        
        # EXPERIMENTAL GROUP C FEATURE: Scaffolding
        if st.session_state.user_group == "Exp_C":
            with st.expander("🤖 AI Learning Assistant"):
                st.info("Based on your pre-test, you should focus on valence electrons.")

# --- PAGE: 4-TIER QUIZ ---
def show_quiz():
    st.header("📝 Diagnostic Assessment")
    
    with st.form("quiz_form"):
        st.write("**Question 1: Why do Sodium and Chlorine react?**")
        
        # Tier 1
        t1 = st.radio("Select the best answer:", ["To fill shells", "To lower potential energy", "To become magnets"])
        # Tier 2
        t2 = st.slider("Confidence in Answer (0-100%):", 0, 100)
        # Tier 3
        t3 = st.radio("Select the reasoning:", ["Atoms have a desire to be stable", "System reaches a minimum energy state", "Opposite charges always attract"])
        # Tier 4
        t4 = st.slider("Confidence in Reasoning (0-100%):", 0, 100)
        
        submitted = st.form_submit_button("Submit Response")
        
        if submitted:
            data = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Student_ID": st.session_state.user_id,
                "Group": st.session_state.user_group,
                "Tier_1_Ans": t1,
                "Tier_2_Conf": t2,
                "Tier_3_Reason": t3,
                "Tier_4_ReasonConf": t4
            }
            if save_response(data):
                st.success("Responses recorded safely.")
                
                # PhD Logic: Misconception detection for Exp_C
                if st.session_state.user_group == "Exp_C" and "desire" in t3 and t4 > 70:
                    st.warning("🚨 AI Insight: You are showing a 'Human-like Desire' misconception about atoms. Atoms follow energy laws, not 'wants'.")

# --- PAGE: ADMIN & SUPERVISOR ---
def show_admin():
    st.header("📊 Research Management Console")
    if st.button("Refresh Master Data"):
        df = conn.read(worksheet="Responses")
        st.dataframe(df)
        
    st.download_button("Download CSV for SPSS/R", "data.csv", "text/csv")

# --- MAIN NAVIGATION ROUTING ---
if not st.session_state.logged_in:
    show_login()
else:
    # Sidebar Navigation based on Role
    pages = ["Home", "Course Content", "4-Tier Quiz"]
    if st.session_state.user_role in ["Admin", "Supervisor"]:
        pages.append("Admin Dashboard")
    
    choice = st.sidebar.selectbox("Navigation", pages)
    
    if choice == "Home": show_home()
    elif choice == "Course Content": show_course()
    elif choice == "4-Tier Quiz": show_quiz()
    elif choice == "Admin Dashboard": show_admin()
