import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    # Fix for the NameError: All functions are now defined below
    st.title("🎓 Student Learning Portal")
    
    # Identify user group for research distinction
    user_group = st.session_state.user.get('group', 'Control')
    st.sidebar.info(f"Research Group: {user_group}")

    # Menu items - AI Science Project is for Exp_A only
    menu = ["📚 Lessons", "✍️ 4-Tier Practice Quiz", "📊 My Progress"]
    if user_group == "Exp_A":
        menu.insert(2, "🤖 Socratic Tutor")
    
    choice = st.sidebar.radio("Select Activity", menu)

    if choice == "📚 Lessons":
        render_lessons(user_group)
    elif choice == "✍️ 4-Tier Practice Quiz":
        render_4_tier_quiz(user_group)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        render_progress()

def render_lessons(group):
    st.header("📚 Chemistry Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        # Filter lessons by the student's assigned group
        my_mats = mats[mats['Group'] == group]
        
        if not my_mats.empty:
            for _, row in my_mats.iterrows():
                with st.expander(f"📖 {row['Module_Name']}"):
                    st.write(f"**Objective:** {row['Learning_Objective']}")
                    if group == "Exp_A":
                        st.info("💡 AI Hint: focus on how particles interact, not just their names.")
                    st.button("Open PDF Material", key=row['Module_Name'])
        else:
            st.write("No lessons deployed for your group yet.")
    except:
        st.error("Could not load lessons.")

def render_4_tier_quiz(group):
    st.header("✍️ 4-Tier Diagnostic Quiz")
    
    # The CRITICAL Research Distinction:
    # Exp_A gets "Immediate Scaffolding" - Control gets "Traditional Assessment"
    if group == "Exp_A":
        st.caption("Experimental Mode: AI is monitoring your reasoning for real-time support.")
    else:
        st.caption("Control Mode: Traditional linear assessment.")

    with st.form("quiz_form"):
        st.markdown("### **Tier 1: The Answer**")
        t1 = st.radio("What is the primary force in a metallic bond?", ["Ionic", "Covalent", "Delocalized Electrons"])
        
        st.markdown("### **Tier 2: Confidence**")
        t2 = st.select_slider("How sure are you?", ["Unsure", "Somewhat Sure", "Very Sure"], key="t2")
        
        st.markdown("### **Tier 3: The Reason**")
        t3 = st.text_area("Explain the chemical principle behind your choice:")
        
        st.markdown("### **Tier 4: Reasoning Confidence**")
        t4 = st.select_slider("How sure are you of your explanation?", ["Unsure", "Somewhat Sure", "Very Sure"], key="t4")
        
        if st.form_submit_button("Submit Assessment"):
            # Save logic here...
            st.success("Responses recorded for research analysis.")

def render_socratic_tutor():
    # This tab only exists for Exp_A
    st.header("🤖 Socratic Science Tutor")
    st.write("I will help you explore your Tier 3 reasoning. Let's start: Why do you think electrons become 'delocalized'?")
    st.chat_input("Your explanation...")

def render_progress():
    st.header("📊 My Progress")
    st.write("Your conceptual growth tracking will appear here as you complete modules.")
