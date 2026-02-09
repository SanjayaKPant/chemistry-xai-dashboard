import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🎓 Student Learning Portal")
    
    # Identify user group
    user_group = st.session_state.user.get('group', 'Control')
    st.sidebar.info(f"Research Group: {user_group}")

    # Menu logic: Socratic Tutor is Exp_A exclusive
    menu = ["📚 Lessons", "✍️ 4-Tier Practice Quiz", "📊 My Progress"]
    if user_group == "Exp_A":
        menu.insert(2, "🤖 Socratic Tutor")
    
    choice = st.sidebar.radio("Select Activity", menu)

    # Fixed NameErrors by defining all functions below
    if choice == "📚 Lessons":
        render_lessons(user_group)
    elif choice == "✍️ 4-Tier Practice Quiz":
        render_4_tier_quiz(user_group)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        render_progress()

def render_lessons(group):
    st.header("📚 Chemistry Modules: Acids, Bases & Salts")
    
    # --- DEMO LESSON 1: THE ARRHENIUS CONCEPT ---
    with st.container(border=True):
        st.subheader("Lesson 1: Introduction to Acids and Bases")
        st.write("""
        **Content:** According to the Arrhenius theory, an Acid is a substance that provides hydrogen ions ($H^+$) in aqueous solution, 
        while a Base provides hydroxide ions ($OH^-$). 
        * *Example Acid:* $HCl \rightarrow H^+ + Cl^-$
        * *Example Base:* $NaOH \rightarrow Na^+ + OH^-$
        """)
        
        if group == "Exp_A":
            with st.expander("💡 AI Learning Scaffold (Socratic Hint)"):
                st.info("Think about the 'Aqueous' part. What would happen to these substances if there was no water present?")
        
        st.button("View Full PDF: Arrhenius Theory", key="pdf_1")

    # --- DEMO LESSON 2: NEUTRALIZATION & SALTS ---
    with st.container(border=True):
        st.subheader("Lesson 2: Neutralization and Salt Formation")
        st.write("""
        **Content:** When an acid and a base react, they neutralize each other to produce a Salt and Water.
        * **Reaction:** $Acid + Base \rightarrow Salt + Water$
        * *Equation:* $HCl + NaOH \rightarrow NaCl + H_2O$
        """)
        
        if group == "Exp_A":
            with st.expander("💡 AI Learning Scaffold (Socratic Hint)"):
                st.info("Consider the ions. If the $H^+$ and $OH^-$ make water, what happens to the remaining $Na^+$ and $Cl^-$ ions in the beaker?")
        
        st.button("View Full PDF: Salts and pH", key="pdf_2")

def render_4_tier_quiz(group):
    st.header("✍️ 4-Tier Practice Quiz")
    st.markdown("### **Tier 1: Content**")
    t1 = st.radio("What ion is responsible for acidic properties in water?", ["$OH^-$", "$H^+$", "$Cl^-$"])
    
    st.markdown("### **Tier 2: Confidence**")
    t2 = st.select_slider("How sure are you?", ["Unsure", "Sure", "Very Sure"], key="t2")
    
    st.markdown("### **Tier 3: Reasoning**")
    t3 = st.text_area("Explain why you chose that ion:")
    
    st.markdown("### **Tier 4: Confidence**")
    t4 = st.select_slider("How sure are you of your reason?", ["Unsure", "Sure", "Very Sure"], key="t4")
    
    if st.form_submit_button("Submit"):
        st.success("Responses recorded for diagnostic analysis.")

def render_socratic_tutor():
    st.header("🤖 Socratic Tutor")
    st.write("Welcome to the Experimental Group's AI assistant. Let's discuss your thoughts on pH.")
    st.chat_input("Explain why you think lemon juice is acidic...")

def render_progress():
    st.header("📊 My Progress")
    st.write("Diagnostic results will be displayed here after completion.")
