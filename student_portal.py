import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    user_group = st.session_state.user.get('group', 'Control')
    st.sidebar.title(f"Group: {user_group}")
    
    menu = ["📚 Science Modules", "🤖 AI Tutor (Exp Only)", "📊 Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "📚 Science Modules":
        render_learning_path(user_group)
    elif choice == "🤖 AI Tutor (Exp Only)":
        if user_group == "Exp_A": render_socratic_tutor()
        else: st.error("Access Denied.")

def render_learning_path(group):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        df.columns = df.columns.str.strip()
        
        my_lessons = df[df['Group'] == group]

        if not my_lessons.empty:
            # Group by Main Lesson
            for main_title, group_df in my_lessons.groupby('Main_Title'):
                st.header(f"📖 Lesson: {main_title}")
                st.info(f"**Outcome:** {group_df.iloc[0]['Learning_Outcomes']}")
                
                for _, row in group_df.iterrows():
                    with st.expander(f"🔹 Concept: {row['Sub_Title']}"):
                        st.write(f"**Objective:** {row['Learning_Objectives']}")
                        
                        # Media Rendering with Thumbnails
                        if row['Video_Links']:
                            for url in row['Video_Links'].split('\n'):
                                if url.strip(): st.video(url.strip())
                        
                        st.write("---")
                        # 4-Tier Assessment Placement
                        st.markdown("### ✍️ Diagnostic Check")
                        with st.form(key=f"form_{row['Sub_Title']}"):
                            st.write(row['Four_Tier_Data'])
                            t1 = st.radio("Tier 1", ["A", "B", "C"], key=f"t1_{row['Sub_Title']}")
                            t3 = st.text_area("Tier 3: Reasoning", key=f"t3_{row['Sub_Title']}")
                            if st.form_submit_button("Submit & Analyze"):
                                st.session_state.current_pivot = row['Socratic_Tree']
                                st.success("Diagnostic Recorded. AI is updated.")
        else:
            st.info("No content assigned yet.")
    except Exception as e: st.error(f"Error: {e}")

def render_socratic_tutor():
    st.header("🤖 Socratic Tutor")
    pivot = st.session_state.get('current_pivot', "Tell me about the concept you just studied.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you think through this concept?"}]

    for m in st.session_state.messages:
        st.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Logic to check IF/THEN from 'pivot' string
        st.rerun()
