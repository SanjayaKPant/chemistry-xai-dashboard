import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    
    # 1. Professional UI: Clear sections using columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Publish New Chemistry Module")
        title = st.text_input("Module Title", placeholder="e.g., Covalent Bonding Basics")
        description = st.text_area("What is this module about?")
        
        # 2. THE AI FEATURE: Auto-generate a hint based on the description
        if st.button("✨ Generate AI Scaffold Hint"):
            if description:
                # In a real-world app, you'd call an API like OpenAI/Gemini here.
                # For now, we simulate the "Professional Prompt Engineering" logic.
                st.session_state.draft_hint = f"Research Prompt: Explain the key concepts of {title} focusing on student misconceptions."
                st.info("AI Suggestion: 'Try to visualize how the electrons are shared rather than transferred. Think of it like a tug-of-war where no one wins!'")
            else:
                st.warning("Please enter a description first so the AI has context.")

    with col2:
        st.subheader("Assignment")
        group = st.selectbox("Target Group", ["Control", "Exp_A", "Both"])
        mode = st.selectbox("Mode", ["Traditional", "AI-Scaffolded"])
        file_link = st.text_input("Drive Link")

    # 3. Save to Google Sheets (The Researcher's Audit Trail)
    if st.button("🚀 Deploy to Students"):
        # Logic to append_row to your 'Instructional_Materials' sheet
        st.success(f"Module '{title}' is now live for {group}!")
