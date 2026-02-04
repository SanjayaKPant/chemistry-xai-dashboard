import streamlit as st
from database_manager import check_login, analyze_reasoning_quality

st.set_page_config(page_title="Chemistry-XAI PhD Portal", layout="wide")

# Initialize login state
if 'user' not in st.session_state:
    st.session_state.user = None

# --- VIEW 1: LOGIN SCREEN ---
if st.session_state.user is None:
    st.title("🧪 Chemistry-XAI Research Portal")
    st.subheader("Grade 9 Learning & Misconception Analysis")
    
    uid = st.text_input("Enter Participant ID (e.g., S001, ADMIN01):").strip().upper()
    
    if st.button("Access Portal"):
        if uid:
            user_data = check_login(uid)
            if user_data:
                st.session_state.user = user_data
                st.rerun()
            else:
                st.error("Access Denied: ID not found. Ensure the Google Sheet has this ID in the 'Participants' tab.")
        else:
            st.warning("Please enter an ID.")

# --- VIEW 2: DASHBOARDS (AFTER LOGIN) ---
else:
    user = st.session_state.user
    role = user['role']
    
    # Sidebar for Navigation
    st.sidebar.title(f"Hello, {user['name']}")
    st.sidebar.info(f"Role: {role} | Group: {user['group']}")
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.rerun()

    # --- ROLE-BASED LOGIC ---
    if role in ["Admin", "Researcher", "Supervisor"]:
        st.title("🔬 Researcher Command Center")
        st.write("Real-time Misconception Analytics for Grade 9 Chemistry.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("System Status", "Live")
        col2.metric("AI Engine", analyze_reasoning_quality([]))
        col3.metric("Data Sync", "Connected")
        
        st.divider()
        st.subheader("Conceptual Change Monitoring")
        st.info("Charts of misconceptions detected in student reasoning will appear here.")

    elif role == "Teacher":
        st.title("👨‍🏫 Teacher Portal")
        st.subheader("Manage AI-Integrated Chemistry Lessons")
        
        uploaded_file = st.file_uploader("Upload Grade 9 Lesson (PDF/Image)", type=['pdf', 'png', 'jpg'])
        if uploaded_file:
            st.success("Lesson uploaded. AI is now generating diagnostic questions...")

    elif role == "Student":
        st.title("🎓 Student Learning Portal")
        st.info(f"Welcome, {user['name']}. Ready to explore Atomic Structure?")
        
        st.subheader("Today's Investigation")
        st.write("Describe why salt dissolves in water. Your answer helps the AI understand how you think!")
        reasoning = st.text_area("Your explanation:")
        if st.button("Submit Reasoning"):
            st.success("Great job! Your explanation has been saved for review.")
