import streamlit as st
from database_manager import check_login, analyze_reasoning_quality, log_temporal_trace

st.set_page_config(page_title="Chemistry PhD Portal", layout="wide")

if 'gate' not in st.session_state: st.session_state.gate = None
if 'user' not in st.session_state: st.session_state.user = None

# --- VIEW 1: THREE GATES ---
if st.session_state.user is None and st.session_state.gate is None:
    st.title("🧪 AI for Science: PhD Portal")
    st.write("Select your access gate:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎓 Student Gate", use_container_width=True):
            st.session_state.gate = "Student"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 Teacher Gate", use_container_width=True):
            st.session_state.gate = "Teacher"
            st.rerun()
    with col3:
        if st.button("🔬 Admin/Researcher Gate", use_container_width=True):
            st.session_state.gate = "Admin"
            st.rerun()

# --- VIEW 2: SECURE LOGIN ---
elif st.session_state.user is None and st.session_state.gate is not None:
    if st.button("← Back"):
        st.session_state.gate = None
        st.rerun()
    
    st.subheader(f"Secure Login: {st.session_state.gate} Portal")
    uid = st.text_input("User ID:").strip().upper()
    pwd = st.text_input("Password:", type="password").strip()
    
    if st.button("Login"):
        user_data = check_login(uid)
        if user_data and user_data['password'] == pwd and user_data['role'] == st.session_state.gate:
            st.session_state.user = user_data
            log_temporal_trace(uid, f"Login to {st.session_state.gate} Gate")
            st.rerun()
        else:
            st.error("Invalid ID, Password, or Gate Permission.")

# --- VIEW 3: DASHBOARDS ---
else:
    user = st.session_state.user
    st.sidebar.success(f"User: {user['name']}")
    if st.sidebar.button("Logout"):
        log_temporal_trace(user['id'], "Logout")
        st.session_state.user = None
        st.session_state.gate = None
        st.rerun()

    if user['role'] == "Admin":
        st.title("🔬 Researcher Command Center")
        st.metric("AI Engine", analyze_reasoning_quality([]))
    elif user['role'] == "Teacher":
        st.title("👨‍🏫 Teacher Portal")
    elif user['role'] == "Student":
        st.title("🎓 Student Portal")
