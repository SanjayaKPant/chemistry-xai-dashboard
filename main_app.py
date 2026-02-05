import streamlit as st
from database_manager import check_login, analyze_reasoning_quality

st.set_page_config(page_title="Chemistry PhD Portal", layout="wide")

# Initialize session state for the specific gate chosen
if 'gate' not in st.session_state:
    st.session_state.gate = None
if 'user' not in st.session_state:
    st.session_state.user = None

# --- VIEW 1: THE THREE GATES ---
if st.session_state.user is None and st.session_state.gate is None:
    st.title("🧪 AI for Science: Entry Portal")
    st.write("Please select your dedicated entry gate:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### 🎓 Students")
        st.write("Access your Chemistry reasoning tasks and AI-integrated lessons.")
        if st.button("Enter Student Gate"):
            st.session_state.gate = "Student"
            st.rerun()

    with col2:
        st.success("### 👨‍🏫 Teachers")
        st.write("Manage Grade 9 modules and review class-wide misconception reports.")
        if st.button("Enter Teacher Gate"):
            st.session_state.gate = "Teacher"
            st.rerun()

    with col3:
        st.warning("### 🔬 Researchers")
        st.write("Admin access for deep analytics and temporal trace monitoring.")
        if st.button("Enter Admin Gate"):
            st.session_state.gate = "Admin"
            st.rerun()

# --- VIEW 2: LOGIN FOR CHOSEN GATE ---
elif st.session_state.user is None and st.session_state.gate is not None:
    st.button("← Back to Gates", on_click=lambda: st.session_state.update({"gate": None}))
    st.header(f"Login: {st.session_state.gate} Portal")
    
    uid = st.text_input(f"Enter {st.session_state.gate} ID:").strip().upper()
    
    if st.button("Verify Identity"):
        res = check_login(uid)
        # Check if user exists AND matches the gate they chose
        if res and (res['role'] == st.session_state.gate or (st.session_state.gate == "Admin" and res['role'] == "Supervisor")):
            st.session_state.user = res
            st.rerun()
        else:
            st.error(f"Access Denied. This ID is not registered for the {st.session_state.gate} gate.")

# --- VIEW 3: THE DASHBOARDS ---
else:
    user = st.session_state.user
    role = user['role']
    
    st.sidebar.success(f"Verified: {user['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.gate = None
        st.rerun()

    if role in ["Admin", "Supervisor"]:
        st.title("🔬 Researcher Dashboard")
        st.write("Tracking misconception frequency across Grade 9 classes.")
        
    elif role == "Teacher":
        st.title("👨‍🏫 Teacher Portal")
        st.write("Welcome to the AI-Integrated Lesson Management System.")

    elif role == "Student":
        st.title("🎓 Student Portal")
        st.write("Ready to investigate the Particulate Nature of Matter?")
