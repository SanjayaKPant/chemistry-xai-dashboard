import streamlit as st
import database_manager as db

st.set_page_config(page_title="Chemistry AI-X Dashboard", layout="wide")

import student_portal
import teacher_portal
import researcher_portal

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🧪 Chemistry Research & Learning Portal")
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Enter ID (e.g., S101, T101)").strip().upper()
    
    if st.button("Login"):
        user_data = db.check_login(user_id)
        if user_data:
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("ID not found. Please check your Participants sheet.")
else:
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.session_state.clear() # Clear chat history on logout
        st.rerun()

    # Routing based on the 'Role' column in your sheet 
    role = st.session_state.user.get('role', 'Student')
    if role == "Student":
        student_portal.show()
    elif role == "Teacher":
        teacher_portal.show()
    elif role == "Researcher":
        researcher_portal.show() 
