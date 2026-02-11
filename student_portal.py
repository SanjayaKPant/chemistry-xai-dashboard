import streamlit as st
import pandas as pd
from database_manager import get_gspread_client, log_student_response, log_temporal_trace

def show():
    user = st.session_state.user
    user_group = user.get('group', 'Control')
    
    st.title(f"🎓 Learning Portal: {user_group} Group")
    
    # Sidebar Navigation
    if user_group == "Exp_A":
        st.sidebar.warning("🛡️ AI-Enabled Mode Active")
        menu = ["📚 Science Modules", "🤖 Socratic Tutor", "📊 My Progress"]
    else:
        st.sidebar.info("📘 Standard Mode Active")
        menu = ["📚 Digital Library", "📊 My Progress"]
        
    choice = st.sidebar.radio("Navigation", menu)

    if choice in ["📚 Science Modules", "📚 Digital Library"]:
        render_learning_path(user_group)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        st.write("Progress tracking is being generated based on your diagnostic scores...")

def render_learning_path(group):
    st.header("📂 Available Concepts")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        # CLEAN HEADERS: Fixes the 'Four_Tier_Data' error automatically
        df.columns = [c.strip().replace(' ', '_') for c in df.columns]
        
        # Filter for the student's group
        my_data = df[df['Group'] == group]

        if not my_data.empty:
            # Group by Main Lesson for better UI
            for main_title, group_df in my_data.groupby('Main_Title'):
                st.subheader(f"📖 Lesson: {main_title}")
                st.caption(f"Goal: {group_df.iloc[0]['Learning_Outcomes']}")
                
                for _, row in group_df.iterrows():
                    with st.expander(f"🔹 CONCEPT: {row['Sub_Title']}"):
                        st.write(f"**Objective:** {row['Learning_Objectives']}")
                        
                        # 1. VISUALS (Videos/Thumbnails)
                        if row['Video_Links']:
                            v_links = row['Video_Links'].split('\n')
                            for link in v_links:
                                if link.strip():
                                    st.video(link.strip())

                        st.markdown("---")
                        
                        # 2. DIAGNOSTIC ASSESSMENT
                        st.subheader("✍️ 4-Tier Diagnostic Check")
                        q_display = row.get('Four_Tier_Data', "No question data provided.")
                        st.info(q_display)
                        
                        with st.form(key=f"quiz_{row['Sub_Title']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                t1 = st.radio("Tier 1: Your Answer", ["Option A", "Option B", "Option C"], key=f"t1_{row['Sub_Title']}")
                                t2 = st.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"], key=f"t2_{row['Sub_Title']}")
                            with col2:
                                t3 = st.text_area("Tier 3: Scientific Reasoning", key=f"t3_{row['Sub_Title']}")
                                t4 = st.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"], key=f"t4_{row['Sub_Title']}")
                            
                            if st.form_submit_button("Submit Response"):
                                log_student_response(st.session_state.user['id'], row['Sub_Title'], group, t1, t2, t3, t4)
                                log_temporal_trace(st.session_state.user['id'], "ASSESSMENT_SUBMIT", row['Sub_Title'])
                                
                                # Store pivot for AI tutor
                                if group == "Exp_A":
                                    st.session_state.current_pivot = row.get('Socratic_Tree', "Ask the student to explain their reasoning.")
                                    st.success("Response logged! Navigate to 'Socratic Tutor' to discuss this concept.")
                                else:
                                    st.success("Response logged! Move to the next concept.")
        else:
            st.warning("No learning modules have been deployed for your group yet.")
            
    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_socratic_tutor():
    st.header("🤖 Socratic Tutor")
    pivot_logic = st.session_state.get('current_pivot', "General Guidance")
    
    st.chat_message("assistant").write(f"I'm ready to discuss the concept. What is your current understanding?")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        st.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Placeholder for Gemini API logic
        st.session_state.messages.append({"role": "assistant", "content": "That's an interesting perspective. How does that fit with the Arrhenius definition?"})
        st.rerun()
