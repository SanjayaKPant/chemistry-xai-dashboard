import streamlit as st
from database_manager import check_login, analyze_reasoning_quality

st.set_page_config(page_title="AI for Science", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🧪 AI for Science: Chemistry Portal")
    uid = st.text_input("Enter ID (e.g., ADMIN01 or S001)").strip().upper()
    if st.button("Login"):
        res = check_login(uid)
        if res:
            st.session_state.user = res
            st.rerun()
        else:
            st.error("Invalid ID.")
else:
    user = st.session_state.user
    role = user['role']
    
    st.sidebar.success(f"Logged in as: {user['name']}")
    st.sidebar.info(f"Role: {role}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- ROLE LOGIC ---
    if role in ["Admin", "Supervisor"]:
        st.title("🔬 Researcher Command Center")
        st.write("Monitor student misconceptions and learning progress in real-time.")
        # Analytics would go here (Data from 'Responses' and 'Temporal_Traces' sheets)
        st.metric("System Status", analyze_reasoning_quality([]))

    elif role == "Teacher":
        st.title("👨‍🏫 Teacher Portal")
        st.subheader("Manage Grade 9 Lessons")
        st.file_uploader("Upload AI-integrated lesson materials", type=['pdf', 'jpg', 'png'])

    elif role == "Student":
        st.title("🎓 Student Learning Portal")
        st.write(f"Welcome to your Grade 9 Chemistry Dashboard, {user['name']}.")
        # Misconception detection tasks would be triggered here
        st.info("Today's Task: Atomic Structure Analysis")
