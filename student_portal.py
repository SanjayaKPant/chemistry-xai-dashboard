import streamlit as st
from database_manager import get_materials_by_group, log_temporal_trace, log_student_response

def show():
    # 1. THE TOOLBAR: Creating a sub-menu within the Student Gate
    # This makes the app feel like a real Learning Management System (LMS)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎒 Student Toolkit")
    menu = st.sidebar.radio(
        "Navigate to:",
        ["📚 Learning Modules", "✍️ Practice Quiz", "🧪 AI Science Project", "📊 My Learning Journey"]
    )

    if menu == "📚 Learning Modules":
        render_learning_modules()
    elif menu == "✍️ Practice Quiz":
        render_practice_quiz()
    elif menu == "🧪 AI Science Project":
        render_ai_project()
    elif menu == "📊 My Learning Journey":
        render_progress_dashboard()

def render_learning_modules():
    st.header("📚 Instructional Materials")
    user = st.session_state.user
    materials = get_materials_by_group(user['group'])

    if not materials:
        st.info("No lessons published yet.")
        return

    for item in materials:
        with st.expander(f"📖 {item['Title']}", expanded=True):
            st.write(item['Description'])
            col1, col2 = st.columns([1, 1])
            with col1:
                st.link_button("📂 Open Study Material", item['File_Link'])
            with col2:
                if user['group'] == "Exp_A" and item.get('Hint'):
                    st.info(f"💡 AI Scaffold: {item['Hint']}")

def render_practice_quiz():
    st.header("✍️ Assessment & Misconception Detection")
    st.markdown("Test your understanding of the latest module.")
    
    # Example MCQ for Misconception Detection (Chemical Bonding)
    with st.form("quiz_form"):
        st.write("**Question 1:** In a covalent bond, what happens to the electrons?")
        choice = st.radio("Select an answer:", [
            "A) They are transferred from one atom to another.",
            "B) They are shared between atoms.",
            "C) They disappear into the nucleus.",
            "D) They are only present in metals."
        ])
        
        submitted = st.form_submit_button("Submit Answer")
        if submitted:
            # Logic: Choice A represents a common misconception (Confusing Ionic with Covalent)
            score = 1 if "B)" in choice else 0
            tag = "Ionic-Covalent Confusion" if "A)" in choice else "None"
            
            # Use our new Assessment_Logs logic!
            log_student_response(
                user_id=st.session_state.user['id'],
                module_id="CHEM_101",
                q_type="MCQ",
                response=choice,
                score=score,
                misconception=tag
            )
            st.success("Response recorded for PhD analysis!")

def render_ai_project():
    st.header("🧪 AI-Integrated Science Project")
    st.info("This section will host your Machine Learning / Deep Learning PBL tools.")
    # Placeholder for the ML/DL models you mentioned
    st.write("Current Phase: Exploring Molecular Prediction Models.")

def render_progress_dashboard():
    st.header("📊 My Learning Journey")
    st.write("Visualize your growth and conceptual change here.")
