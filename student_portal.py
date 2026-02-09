import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client, log_student_response

def show():
    st.title("🎓 Student Learning Portal")
    
    # Sidebar Info
    st.sidebar.success(f"Group: {st.session_state.user['group']}")
    
    menu = ["📚 Lessons", "✍️ 4-Tier Practice Quiz", "🤖 Socratic Tutor", "📊 My Progress"]
    choice = st.sidebar.radio("Select Activity", menu)

    if choice == "📚 Lessons":
        render_lessons()
    elif choice == "✍️ 4-Tier Practice Quiz":
        render_4_tier_quiz()
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        render_progress()

def render_4_tier_quiz():
    st.header("🧪 4-Tier Conceptual Assessment")
    st.info("Answer carefully. Your confidence levels help the AI guide you better.")

    with st.form("quiz_form"):
        # TIER 1: Content Answer
        st.markdown("### **Tier 1: Content Question**")
        t1_ans = st.radio("What happens to water molecules when water boils?", 
                         ["They break into H and O atoms", "They move further apart", "They get larger"])

        # TIER 2: Content Confidence
        st.markdown("### **Tier 2: Confidence (Answer)**")
        t2_conf = st.select_slider("How sure are you about your answer?", 
                                  options=["Very Unsure", "Unsure", "Sure", "Very Sure"], key="t2")

        # TIER 3: Reasoning
        st.markdown("### **Tier 3: Reasoning**")
        t3_reas = st.radio("Why did you choose that answer?", 
                          ["Heat breaks chemical bonds", "Increased kinetic energy overcomes intermolecular forces", "Molecules expand when heated"])

        # TIER 4: Reasoning Confidence
        st.markdown("### **Tier 4: Confidence (Reasoning)**")
        t4_conf = st.select_slider("How sure are you about your reason?", 
                                  options=["Very Unsure", "Unsure", "Sure", "Very Sure"], key="t4")

        submit_quiz = st.form_submit_button("Submit Assessment")

        if submit_quiz:
            # 🔬 RESEARCH LOGIC: Perform Diagnostic
            result, tag = perform_diagnostic(t1_ans, t2_conf, t3_reas, t4_conf)
            
            # Save to Assessment_Logs with all 10 headers
            success = log_student_response(
                st.session_state.user['id'],
                "WATER_BOIL_01",
                t1_ans, t2_conf, t3_reas, t4_conf,
                result, tag, st.session_state.user['group']
            )
            
            if success:
                st.success(f"Assessment Logged! Result: {result}")
                if st.session_state.user['group'] == "Exp_A":
                    st.write("🤖 **Socratic Tutor is now ready to discuss your reasoning!**")

def perform_diagnostic(t1, t2, t3, t4):
    """
    🔬 PhD Research Logic: 
    Categorizes the student based on 4-tier response patterns.
    """
    # Simplified logic for demonstration (customize based on your key)
    correct_t1 = "They move further apart"
    correct_t3 = "Increased kinetic energy overcomes intermolecular forces"
    
    is_high_conf = t2 in ["Sure", "Very Sure"] and t4 in ["Sure", "Very Sure"]
    
    if t1 == correct_t1 and t3 == correct_t3 and is_high_conf:
        return "Scientific Knowledge", "None"
    elif t1 == correct_t1 and t3 != correct_t3 and is_high_conf:
        return "Misconception", "Reasoning-Gap"
    elif t1 != correct_t1 and is_high_conf:
        return "Misconception", "Fundamental-Error"
    else:
        return "Lack of Knowledge", "Uncertain"

def render_socratic_tutor():
    st.header("🤖 Socratic Chemistry Assistant")
    
    if st.session_state.user['group'] == "Control":
        st.warning("The AI Tutor is currently only available for the Experimental Group.")
        return

    # Socratic logic: Ask "Why" and "How" based on Tier 3
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I noticed your reasoning about heat breaking bonds. If that happened, what would happen to the identity of the water?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        # AI Response logic (to be linked to Gemini)
        st.rerun()
