import streamlit as st
import database_manager as db

st.set_page_config(page_title="Chemistry PhD Research Portal", layout="wide")

import student_portal
import teacher_portal
import researcher_portal

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🧪 Chemistry AI-X Research Portal")
    st.markdown("### Evidence-Based Socratic Learning System | नेपाली र अंग्रेजी")
    
    col1, _ = st.columns([1, 1])
    with col1:
        user_id = st.text_input("Enter User ID (eg: STD_1001, T101)").strip().upper()
    
    if st.button("Login | लगइन"):
        user_data = db.check_login(user_id)
        if user_data:
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("ID not found. Please verify with the Participants database.")
else:
    # Sidebar logout
    st.sidebar.title(f"👤 {st.session_state.user.get('Name')}")
    role = str(st.session_state.user.get('Role', 'Student')).strip()
    st.sidebar.write(f"**Role:** {role}")
    
    if st.sidebar.button("Logout | बाहिरिनुहोस्"):
        st.session_state.clear()
        st.rerun()

    # PhD Routing Logic
    if role in ["Researcher", "Supervisor", "Admin"]:
        researcher_portal.show()
    elif role in ["Teacher", "Head Teacher"]:
        teacher_portal.show()
    else:
        student_portal.show()
