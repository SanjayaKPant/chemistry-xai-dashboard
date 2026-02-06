import streamlit as st

# 1. MANDATORY INITIALIZATION (Prevents NameError/AttributeError)
if 'user' not in st.session_state:
    st.session_state.user = None
if 'gate' not in st.session_state:
    st.session_state.gate = None

st.set_page_config(page_title="Chemistry PhD Portal", layout="wide")

# 2. SECURE IMPORTS (Prevents IndentationError from crashing the app)
try:
    import student_portal
    import teacher_portal
    import researcher_portal
except ImportError as e:
    st.error(f"Module Loading Error: {e}")

# 3. GATEWAY LOGIC
if st.session_state.user is None:
    st.title("🧪 Chemistry Research Portal")
    gate_choice = st.sidebar.selectbox("Select Gate", ["Student", "Teacher", "Researcher"])
    
    # Simple login simulation for your current build
    if st.sidebar.button("Login"):
        # Defaulting to Exp_A for your testing
        st.session_state.user = {"id": "STD_1001", "name": "Scholar", "group": "Exp_A"}
        st.session_state.gate = gate_choice
        st.rerun()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.gate}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # Routing to the correct portal function
    if st.session_state.gate == "Student":
        student_portal.show()
    elif st.session_state.gate == "Teacher":
        teacher_portal.show()
    elif st.session_state.gate == "Researcher":
        researcher_portal.show()
