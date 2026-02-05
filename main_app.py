import streamlit as st
from database_manager import check_login, log_temporal_trace
# Import the new portfolios
try:
    from student_portal import show_student_portal
    from teacher_portal import show_teacher_portal
    from researcher_portal import show_researcher_portal
except ImportError:
    # This prevents the app from crashing if the files are still empty
    def show_student_portal(u): st.title("Student Portal - Under Construction")
    def show_teacher_portal(u): st.title("Teacher Portal - Under Construction")
    def show_researcher_portal(u): st.title("Researcher Portal - Under Construction")

# ... (Keep your existing Gate and Login code here) ...

# --- VIEW 3: THE PORTFOLIO ROUTER ---
else:
    user = st.session_state.user
    role = user['role'] #
    
    # Sidebar remains consistent for all users
    st.sidebar.success(f"Logged in: {user['name']}")
    if st.sidebar.button("Logout"):
        log_temporal_trace(user['id'], "User Logout")
        st.session_state.user = None
        st.session_state.gate = None
        st.rerun()

    # Route to the correct portfolio file
    if role == "Admin":
        show_researcher_portal(user)
    elif role == "Teacher":
        show_teacher_portal(user)
    elif role == "Student":
        show_student_portal(user)
