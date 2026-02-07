import streamlit as st
import pandas as pd
from database_manager import get_materials_by_group, log_student_response

def show():
    # --- SIDEBAR TOOLBAR (The Khanmingo Style) ---
    st.sidebar.header(f"👋 Welcome, {st.session_state.user['id']}")
    st.sidebar.markdown("---")
    
    # Navigation ToolBar
    menu = st.sidebar.radio(
        "Learning Menu",
        ["📚 Lessons", "📝 Assessment (Quizzes)", "🧪 AI Project (PBL)", "📊 My Progress"]
    )

    if menu == "📚 Lessons":
        render_lessons()
    elif menu == "📝 Assessment (Quizzes)":
        render_assessment()
    elif menu == "🧪 AI Project (PBL)":
        render_ai_pbl()

def render_lessons():
    st.title("📚 Instructional Materials")
    user_group = st.session_state.user['group']
    materials = get_materials_by_group(user_group)

    if not materials:
        st.info("No lessons published for your group yet.")
        return

    for item in materials:
        with st.container(border=True):
            st.subheader(item['Title'])
            st.write(item['Description'])
            
            # Plan B: AI Scaffolded Hint
            if user_group == "Exp_A" and item.get('Hint'):
                with st.expander("💡 View AI Scaffolding Hint"):
                    st.info(item['Hint'])
            
            st.link_button("📂 View PDF", item['File_Link'])

def render_assessment():
    st.title("📝 Assessment & Misconception Lab")
    st.write("Complete this to help us understand your learning journey.")

    # Dynamic Quiz for Misconception Detection
    with st.form("quiz_one"):
        st.markdown("### Question 1: Molecular Geometry")
        st.write("What determines the shape of a molecule according to VSEPR theory?")
        ans = st.radio("Select one:", [
            "A) The color of the atoms.",
            "B) Repulsion between electron pairs.",
            "C) The total weight of the molecule.",
            "D) The size of the container."
        ])
        
        if st.form_submit_button("Submit Response"):
            # Scoring Logic
            score = 1 if "B)" in ans else 0
            # Misconception Tagging (PhD Research Data)
            m_tag = "Size-Shape Confusion" if "D)" in ans else "None"
            
            success = log_student_response(
                user_id=st.session_state.user['id'],
                module_id="MOD_VSEPR",
                q_type="MCQ",
                response=ans,
                score=score,
                misconception=m_tag
            )
            if success:
                st.success("Result logged in 'Assessment_Logs'!")

def render_ai_pbl():
    st.title("🧪 AI-Integrated Science Project")
    st.info("Welcome to the Project-Based Learning (PBL) Zone.")
    
    st.markdown("### 🤖 Molecular Property Predictor (ML Demo)")
    st.write("Input molecular data below to see how our AI predicts boiling points.")
    
    molecular_weight = st.number_input("Enter Molecular Weight", 0, 500)
    if st.button("Run AI Prediction"):
        # This is where your ML/DL models will eventually sit
        prediction = molecular_weight * 0.5 + 10 # Simulated ML Logic
        st.metric("Predicted Boiling Point (°C)", f"{prediction}")
        st.write("**Explainable AI (XAI) Note:** The model prioritized weight over bond type for this prediction.")
