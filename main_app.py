import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- DATABASE VALIDATOR (PhD INTEGRITY LAYER) ---
def validate_database_structure(conn):
    """
    Ensures the Google Sheet is healthy and ready for PhD-grade data.
    If headers are missing, the app stops to prevent corrupted data collection.
    """
    required_tabs = {
        "Participants": ["User_ID", "Name", "Role", "Group"],
        "Responses": ["Timestamp", "User_ID", "Lesson", "Tier_1", "Tier_2", "Tier_3", "Tier_4"]
    }
    
    for tab, required_columns in required_tabs.items():
        try:
            # Live check of the spreadsheet headers
            df = conn.read(worksheet=tab, ttl=0)
            missing = [col for col in required_columns if col not in df.columns]
            
            if missing:
                st.error(f"❌ DATABASE ERROR: Tab '{tab}' is missing columns: {missing}")
                st.info("PhD Supervisor Note: Please fix your Google Sheet headers before proceeding.")
                st.stop()
                
        except Exception:
            st.error(f"⚠️ CONNECTION ERROR: Cannot find tab '{tab}' in your Google Sheet.")
            st.stop()

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="AI-Chem Research Portal", layout="wide")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None # Store the whole row of user info

# --- NEW: DATABASE AUTHENTICATION FUNCTION ---
def authenticate_user(user_id):
    try:
        # Read the Participants sheet
        users_df = conn.read(worksheet="Participants")
        
        # Look for the user_id in the first column
        user_row = users_df[users_df['User_ID'] == user_id]
        
        if not user_row.empty:
            return user_row.iloc[0].to_dict() # Return user details as a dictionary
        return None
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

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

# --- UPDATED LOGIN PAGE ---
def show_login():
    st.title("🇳🇵 PhD Research: AI in Chemistry")
    st.subheader("Login with your Research ID")
    
    with st.container(border=True):
        input_id = st.text_input("Research ID:", placeholder="e.g. S001")
        if st.button("Enter Portal"):
            user_info = authenticate_user(input_id)
            if user_info:
                st.session_state.logged_in = True
                st.session_state.user_data = user_info
                st.success(f"Welcome back, {user_info['Name']}!")
                st.rerun()
            else:
                st.error("Access Denied: ID not found in the research database.")

# --- PAGE: HOME (Welcome & Ethics) ---
def show_home():
    # Fetching data from the session state (populated during login)
    user = st.session_state.user_data
    
    st.header(f"Welcome, {user.get('Name', 'Participant')}")
    st.write(f"**Research Group:** {user.get('Group', 'Not Assigned')}")
    st.write(f"**Your Role:** {user.get('Role', 'Student')}")
    
    st.markdown("""
    ---
    ### 📜 Research Participant Information
    This study investigates how AI-integrated scaffolding helps clarify misconceptions in **Atomic Structure**.
    
    **Your Privacy:**
    * Data is anonymized for PhD research purposes.
    * You can withdraw at any time.
    """)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_data = None
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
    st.header("📊 PhD Research Management Console")
    st.info("Direct Access for Lead Researcher and Supervisors")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ View Participant List"):
            participants = conn.read(worksheet="Participants")
            st.dataframe(participants)
            
    with col2:
        if st.button("📥 Download Research Data"):
            responses = conn.read(worksheet="Responses")
            st.dataframe(responses)
            # Standard CSV export for SPSS/R analysis
            csv = responses.to_csv(index=False).encode('utf-8')
            st.download_button("Download for Statistical Analysis", data=csv, file_name="chemistry_research_data.csv", mime='text/csv')

# --- MAIN NAVIGATION ROUTING (Corrected) ---
if not st.session_state.logged_in:
    show_login()
else:
    # 1. Safely extract user info from the session state
    user_info = st.session_state.user_data
    role = user_info.get('Role', 'Student') # Default to Student if not found
    group = user_info.get('Group', 'Control')
    
    # 2. Build Sidebar Navigation
    st.sidebar.title("🔬 Research Menu")
    st.sidebar.write(f"Logged in as: **{user_info.get('Name')}**")
    
    pages = ["Home", "Course Content", "4-Tier Quiz"]
    
    # 3. Add Admin/Supervisor pages only if they have the right role
    if role in ["Admin", "Supervisor"]:
        pages.append("Admin Dashboard")
    
    choice = st.sidebar.selectbox("Go to:", pages)
    
    # 4. Display the chosen page
    if choice == "Home": 
        show_home()
    elif choice == "Course Content": 
        show_course()
    elif choice == "4-Tier Quiz": 
        show_quiz()
    elif choice == "Admin Dashboard": 
        show_admin()
