import streamlit as st
# Only import what we defined in Step 1
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
            st.error("Login failed. Check ID and Sheet Permissions.")
else:
    user = st.session_state.user
    role = user['role']
    
    st.sidebar.success(f"User: {user['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # Dashboard Logic based on your sheet roles
    if role in ["Admin", "Supervisor"]:
        st.title("🔬 Researcher Dashboard")
        st.metric("AI Engine", analyze_reasoning_quality([]))
    elif role == "Student":
        st.title("🎓 Student Portal")
        st.write("Welcome to the Chemistry Reasoning Task.")
