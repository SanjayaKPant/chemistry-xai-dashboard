import streamlit as st
import database_manager as db

# Page Config must be the first command
st.set_page_config(page_title="Chemistry PhD Research Portal", layout="wide")

# Import the portal modules
import student_portal
import teacher_portal
import researcher_portal

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🧪 Chemistry AI-X Research Portal")
    st.markdown("### Evidence-Based Socratic Learning System")
    
    col1, _ = st.columns([1, 1])
    with col1:
        user_id = st.text_input("Enter Researcher/User ID").strip().upper()
    
    if st.button("Login"):
        user_data = db.check_login(user_id)
        if user_data:
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("ID not found. Please verify with the Participants database.")
else:
    # Sidebar logout and info
    st.sidebar.title(f"👤 {st.session_state.user.get('Name')}")
    st.sidebar.write(f"**Role:** {st.session_state.user.get('Role')}")
    
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.session_state.clear()
        st.rerun()

    # --- PhD ROUTING LOGIC ---
    # We force a strict check to prevent role-bleeding
    role = str(st.session_state.user.get('Role', 'Student')).strip()

    if role == "Researcher" or role == "Supervisor":
        researcher_portal.show()
    elif role == "Teacher":
        teacher_portal.show()
    else:
        student_portal.show()
