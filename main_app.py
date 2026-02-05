import streamlit as st
from database_manager import check_login, log_temporal_trace

# --- SAFE IMPORTS ---
try:
    import teacher_portal
    import student_portal
    import researcher_portal
except Exception as e:
    st.error(f"Error importing modules: {e}")

st.set_page_config(page_title="Chemistry PhD Portal", layout="wide")

if 'gate' not in st.session_state: st.session_state.gate = None
if 'user' not in st.session_state: st.session_state.user = None

# --- VIEW 1: GATES ---
if st.session_state.user is None and st.session_state.gate is None:
    st.title("🧪 Chemistry Research Portal")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 Student Gate"): 
            st.session_state.gate = "Student"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 Teacher Gate"): 
            st.session_state.gate = "Teacher"
            st.rerun()
    with col3:
        if st.button("🔬 Admin Gate"): 
            st.session_state.gate = "Admin"
            st.rerun()

# --- VIEW 2: LOGIN ---
elif st.session_state.user is None and st.session_state.gate is not None:
    if st.button("← Back"):
        st.session_state.gate = None
        st.rerun()
    st.subheader(f"Login: {st.session_state.gate}")
    uid = st.text_input("ID").strip().upper()
    pwd = st.text_input("Password", type="password")
    if st.button("Enter"):
        user_data = check_login(uid)
        if user_data and user_data['password'] == pwd and user_data['role'] == st.session_state.gate:
            st.session_state.user = user_data
            log_temporal_trace(uid, "Login")
            st.rerun()
        else:
            st.error("Invalid Login")

# --- VIEW 3: THE ROUTER ---
else:
    user = st.session_state.user
    role = user['role'] #
    
    st.sidebar.write(f"Logged in as: {user['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.gate = None
        st.rerun()

    # Call the functions only if they exist in the files
    try:
        if role == "Teacher":
            teacher_portal.show_teacher_portal(user)
        elif role == "Student":
            student_portal.show_student_portal(user)
        elif role == "Admin":
            researcher_portal.show_researcher_portal(user)
    except AttributeError:
        st.warning(f"The {role} portal file is currently empty or missing the 'show' function.")
