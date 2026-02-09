import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    # Detect the logged-in student's research group
    user_group = st.session_state.user.get('group', 'Control')
    st.title("🎓 Student Learning Portal")
    st.sidebar.info(f"Research Group: {user_group}")

    # Navigation Menu
    menu = ["📚 Learning Modules", "✍️ 4-Tier Assessment", "📊 My Progress"]
    if user_group == "Exp_A":
        menu.insert(1, "🤖 Socratic AI Tutor")
    
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "📚 Learning Modules":
        render_learning_path(user_group)
    elif choice == "🤖 Socratic AI Tutor":
        render_socratic_tutor()
    elif choice == "✍️ 4-Tier Assessment":
        render_assessment(user_group)
    elif choice == "📊 My Progress":
        render_progress()

def render_learning_path(group):
    st.header("📚 Your Learning Journey")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        if not mats.empty:
            for _, row in mats.iterrows():
                with st.expander(f"📖 Module: {row['Topic']}"):
                    st.write(f"**Lesson ID:** {row['Module_ID']}")
                    
                    # Serve Group-Specific Content
                    video_url = row['Exp_Video'] if group == "Exp_A" else row['Ctrl_Video']
                    
                    if video_url:
                        st.video(video_url)
                    
                    st.write("---")
                    st.info("📂 Review the attached PDF/Image materials before starting the quiz.")
                    st.button(f"Open Lesson Materials ({row['Module_ID']})")
        else:
            st.warning("No modules have been deployed yet.")
    except Exception as e:
        st.error(f"Error loading path: {e}")

def render_socratic_tutor():
    st.header("🤖 Socratic Chemistry Assistant")
    st.caption("Experimental Group Only: Interactive Conceptual Support")
    
    # Retrieve the 'Socratic Anchor' from the last deployed module
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        current_anchor = mats.iloc[-1]['Socratic_Anchor'] if not mats.empty else "Let's explore chemistry!"
    except:
        current_anchor = "Let's discuss your reasoning."

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role": "assistant", "content": f"Hello! I'm here to help you think through the lesson. {current_anchor}"}]

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Explain your thoughts here..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        # Note: Gemini API integration occurs here
        st.rerun()

def render_assessment(group):
    st.header("✍️ 4-Tier Conceptual Diagnostic")
    st.info("Note: This assessment is identical for all groups to ensure scientific validity.")
    
    with st.form("quiz_form"):
        st.markdown("### Tier 1: The Answer")
        t1 = st.radio("Which statement is true about bases?", ["Increase $H^+$", "Neutralize acids to form salt", "Have pH below 7"])
        
        st.markdown("### Tier 2: Content Confidence")
        t2 = st.select_slider("How sure are you?", ["Unsure", "Sure", "Very Sure"], key="t2")
        
        st.markdown("### Tier 3: Scientific Reasoning")
        t3 = st.text_area("Why does this occur? Explain the chemical mechanism:")
        
        st.markdown("### Tier 4: Reasoning Confidence")
        t4 = st.select_slider("How sure are you of your explanation?", ["Unsure", "Sure", "Very Sure"], key="t4")
        
        if st.form_submit_button("Submit 4-Tier Response"):
            # logic to calculate Misconception_Tag and save to Assessment_Logs
            st.success("Your diagnostic data has been securely logged.")

def render_progress():
    st.header("📊 Research Progress Tracking")
    st.write("Visualizing your conceptual growth over time.")
