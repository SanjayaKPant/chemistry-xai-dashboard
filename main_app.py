import streamlit as st
from database_manager import check_login, analyze_reasoning_quality

st.set_page_config(page_title="Chemistry AI Portal", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🧪 Chemistry-XAI Learning Portal")
    uid = st.text_input("Enter Participant/Staff ID:").strip().upper()
    if st.button("Login"):
        user_data = check_login(uid)
        if user_data:
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("Access Denied. Please check your ID.")
else:
    user = st.session_state.user
    role = user['role']
    
    st.sidebar.title(f"Welcome, {user['name']}")
    st.sidebar.info(f"Role: {role}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- ROLE-BASED DASHBOARD LOGIC ---
    if role in ["Admin", "Supervisor"]:
        st.title("🔬 Researcher Analytics Dashboard")
        st.write("Tracking conceptual change and misconception frequency.")
        st.metric("System Health", analyze_reasoning_quality([]))
        # Future: Insert plotly charts here showing student progress

    elif role == "Teacher":
        st.title("👨‍🏫 Teacher Portal")
        st.subheader("Chemistry Lesson Management (Grade 9)")
        st.file_uploader("Upload New AI-Integrated Lesson Plan", type=['pdf', 'docx'])

    elif role == "Student":
        st.title("🎓 Student Learning Portal")
        st.write(f"Hello {user['name']}, let's explore Chemistry!")
        st.info("Module 1: Atomic Structure - Particulate Nature of Matter")
