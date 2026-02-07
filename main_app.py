import streamlit as st

# MUST be the first line
st.set_page_config(page_title="Chemistry AI-X Dashboard", layout="wide")

# 1. Professional Import Block
import student_portal
import teacher_portal
import researcher_portal

# 2. Session Initialization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'gate' not in st.session_state:
    st.session_state.gate = None

# 3. Navigation Gate
if st.session_state.user is None:
    st.title("🧪 Chemistry Research & Learning Portal")
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Enter Student/Teacher ID")
        gate_choice = st.selectbox("Select Access Gate", ["Student", "Teacher", "Researcher"])
    
    if st.button("Login"):
        # Simulated login - ensure group logic matches your Spreadsheet 'Participants' tab
        st.session_state.user = {"id": user_id, "group": "Exp_A"} 
        st.session_state.gate = gate_choice
        st.rerun()
else:
    # Sidebar logout
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.rerun()

    # Routing
    if st.session_state.gate == "Student":
        student_portal.show()
    elif st.session_state.gate == "Teacher":
        teacher_portal.show()
    elif st.session_state.gate == "Researcher":
        researcher_portal.show()
