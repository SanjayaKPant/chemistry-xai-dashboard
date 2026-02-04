import streamlit as st
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
            st.error("ID not found or Database Error. Check your Secrets and Tab name.")
else:
    user = st.session_state.user
    role = user['role']
    
    st.sidebar.success(f"User: {user['name']}")
    st.sidebar.info(f"Role: {role}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- ROLE-BASED DASHBOARDS ---
    if role in ["Admin", "Supervisor"]:
        st.title("🔬 Researcher Command Center")
        st.subheader("Conceptual Change Analytics")
        st.metric("AI Engine Status", analyze_reasoning_quality([]))
        st.write("Monitoring real-time student misconceptions...")
        # Add a placeholder for your data charts
        st.bar_chart({"Misconceptions": [5, 12, 3], "Topic": ["Atoms", "Bonds", "Matter"]})

    elif role == "Teacher":
        st.title("👨‍🏫 Teacher Portal")
        st.subheader("Upload Grade 9 Chemistry Lessons")
        st.file_uploader("Upload Lesson PDF/Image", type=['pdf', 'jpg', 'png'])

    elif role == "Student":
        st.title("🎓 Student Learning Portal")
        st.write(f"Welcome, {user['name']}. Let's study the Particulate Nature of Matter.")
        # Reasoning sandbox for misconception detection
        st.text_area("Explain why a balloon shrinks in a cold freezer:")
        if st.button("Submit Explanation"):
            st.success("Reasoning saved. AI is analyzing your mental model.")
