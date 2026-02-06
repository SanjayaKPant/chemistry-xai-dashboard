import streamlit as st

# Mandatory Session State Initialization
if 'user' not in st.session_state: st.session_state.user = None
if 'gate' not in st.session_state: st.session_state.gate = None

st.set_page_config(page_title="Chemistry PhD Portal", layout="wide")

try:
    import student_portal, teacher_portal, researcher_portal
except ImportError as e:
    st.error(f"Module Error: {e}")

if st.session_state.user is None:
    st.title("🎓 PhD Research Portal")
    # Gate Selection Logic
    gate = st.sidebar.selectbox("Gate", ["Student", "Teacher", "Researcher"])
    if st.sidebar.button("Login"):
        st.session_state.user = {"id": "PHD_01", "group": "Exp_A"}
        st.session_state.gate = gate
        st.rerun()
else:
    # Portal Routing
    if st.session_state.gate == "Student": student_portal.show()
    elif st.session_state.gate == "Teacher": teacher_portal.show()
    elif st.session_state.gate == "Researcher": researcher_portal.show()
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
