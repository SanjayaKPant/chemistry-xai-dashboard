import streamlit as st
from database_manager import check_login, analyze_reasoning_quality

st.set_page_config(page_title="Chemistry PhD Portal", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🧪 AI for Science: PhD Portal")
    uid = st.text_input("Enter Participant ID:").strip().upper()
    if st.button("Login"):
        res = check_login(uid)
        if res:
            st.session_state.user = res
            st.rerun()
        else:
            st.error("ID not found in Participants sheet.")
else:
    user = st.session_state.user
    role = user['role']
    
    st.sidebar.success(f"Logged in: {user['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    if role in ["Admin", "Researcher", "Supervisor"]:
        st.title("🔬 Researcher Analytics Dashboard")
        st.info("Tracking misconception frequency across Grade 9 classes.")
        st.metric("AI Analysis Status", analyze_reasoning_quality([]))
        
    elif role == "Teacher":
        st.title("👨‍🏫 Teacher Lesson Portal")
        st.file_uploader("Upload Chemistry Lesson (PDF)", type=['pdf'])

    elif role == "Student":
        st.title("🎓 Student Learning Portal")
        st.write("Today's Task: The Particulate Nature of Matter")
