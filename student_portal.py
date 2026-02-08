import streamlit as st
import pandas as pd
from database_manager import get_materials_by_group, log_student_response

def show():
    # --- KANMINGO STYLE TOOLBAR ---
    st.sidebar.markdown("### 🎒 Student Dashboard")
    st.sidebar.info(f"Group: {st.session_state.user['group']}")
    
    # Navigation Menu
    menu = st.sidebar.radio(
        "Select Activity",
        ["📚 Lessons", "✍️ Practice Quiz", "🧪 AI Science Project", "📊 My Stats"]
    )

    st.sidebar.markdown("---")
    
    # Routing the views
    if menu == "📚 Lessons":
        render_lessons()
    elif menu == "✍️ Practice Quiz":
        render_quiz()
    elif menu == "🧪 AI Science Project":
        render_ai_pbl()
    elif menu == "📊 My Stats":
        st.title("📊 Your Learning Journey")
        st.write("Coming Soon: Track your conceptual change over time!")

def render_lessons():
    st.title("📚 Chemistry Modules")
    materials = get_materials_by_group(st.session_state.user['group'])
    
    if not materials:
        st.info("Your teacher hasn't published any lessons for your group yet.")
        return

    for item in materials:
        with st.container(border=True):
            st.subheader(item['Title'])
            st.write(item['Description'])
            
            # THE AI SCAFFOLD (Experimental Group Only)
            if st.session_state.user['group'] == "Exp_A" and item.get('Hint'):
                with st.expander("💡 View AI Learning Scaffold"):
                    st.info(item['Hint'])
            
            st.link_button("📖 Open PDF Material", item['File_Link'])

def render_quiz():
    st.title("✍️ MCQ & Misconception Lab")
    st.write("Test your knowledge of Molecular Structures.")

    with st.form("chemistry_quiz"):
        st.markdown("**Question:** Why is a water molecule 'bent' rather than linear?")
        answer = st.radio("Choose the best explanation:", [
            "A) Because hydrogen atoms are heavy.",
            "B) Due to repulsion between lone electron pairs on Oxygen.",
            "C) Because the container pushes on the molecule.",
            "D) It's just random."
        ])
        
        if st.form_submit_button("Submit to Assessment_Logs"):
            # Scoring & Misconception Tagging
            is_correct = 1 if "B)" in answer else 0
            tag = "VSEPR Repulsion Error" if "C)" in answer else "None"
            
            success = log_student_response(
                user_id=st.session_state.user['id'],
                module_id="CHEM_WATER_01",
                q_type="MCQ",
                response=answer,
                score=is_correct,
                misconception=tag
            )
            if success:
                st.success("Analysis complete! Your response is logged.")

def render_ai_pbl():
    st.title("🧪 AI-Integrated Project (PBL)")
    st.markdown("### 🤖 Molecular Property Predictor")
    st.write("Using Machine Learning to explore chemical properties.")
    
    mol_weight = st.slider("Molecular Weight", 1.0, 300.0, 18.0)
    
    if st.button("Predict Boiling Point (ML Model)"):
        # This simulates a Deep Learning model output
        prediction = (mol_weight * 1.5) + 20 
        st.metric("Predicted Boiling Point", f"{round(prediction, 2)} °C")
        st.caption("XAI Insight: Model weight assigned 85% importance to molecular mass.")

import streamlit as st

def render_socratic_chat():
    st.markdown("### 🤖 Socratic Chemistry Tutor")
    st.caption("Let's look at your reasoning from the last quiz.")

    # Khanmingo Style: AI references the student's Tier 3 'Reason'
    # We will eventually pull this live from your Google Sheet
    last_reason = "Nucleus is at the center" # Placeholder for Tier 3 data
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"You mentioned that '{last_reason}'. If that's the case, what do you think keeps the electrons from flying away?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Think about the forces involved..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        # The AI asks another question instead of giving the answer
        response = "Interesting! Does that force come from the protons or the neutrons?"
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
