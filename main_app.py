import streamlit as st
from database_manager import check_login # and your other functions

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    # --- LOGIN PAGE ---
    st.title("🧪 AI for Science: Chemistry Portal")
    user_id = st.text_input("Enter ID").upper()
    if st.button("Login"):
        user_data = check_login(user_id)
        if user_data:
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("ID not found.")

else:
    role = st.session_state.user['role']
    name = st.session_state.user['name']

    # --- SHARED SIDEBAR ---
    st.sidebar.title(f"Welcome, {name}")
    st.sidebar.info(f"Role: {role}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- ROLE-BASED DASHBOARDS ---
    if role == "Admin" or role == "Researcher":
        st.title("🔬 Researcher Command Center")
        st.write("Monitoring conceptual change and system metrics.")
        # Add metrics for total responses and detected misconceptions
        col1, col2 = st.columns(2)
        col1.metric("Active Students", "45") 
        col2.metric("Misconceptions Found", "12")

    elif role == "Teacher":
        st.title("👨‍🏫 Teacher Upload Portal")
        st.subheader("Upload Grade 9 Chemistry Lessons")
        uploaded_file = st.file_uploader("Upload PDF or Image", type=['pdf', 'png', 'jpg'])
        if uploaded_file:
            st.success("Lesson uploaded to Google Drive folder.")

    elif role == "Student":
        st.title("🎓 Student Learning Portal")
        st.info("Grade 9 Chemistry: Atomic Structure & Bonding")
        # The student sees the actual learning content here
        st.video("https://www.youtube.com/watch?v=your_lesson_video")
