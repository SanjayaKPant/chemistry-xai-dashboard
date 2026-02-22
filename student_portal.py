import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    user = st.session_state.user
    user_school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "📝 Assignments", "🤖 Socratic AI Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigate", menu)

    if choice == "🏠 Dashboard":
        render_dashboard()
    elif choice == "📚 Learning Modules":
        render_modules(user_school)
    elif choice == "📝 Assignments":
        render_assignments(user_school)
    elif choice == "🤖 Socratic AI Tutor":
        render_ai_chat()
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard():
    st.title("Welcome to Chemistry Hub")
    st.subheader("Your Learning Milestone")
    st.progress(0.4)
    st.info("💡 Tip: Complete your Diagnostic Questions in 'Learning Modules' to unlock the AI Tutor.")

def render_modules(school):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # --- HEADER NORMALIZATION FIX ---
        df.columns = [c.strip().upper() for c in df.columns]
        my_lessons = df[df['GROUP'].str.strip().str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('SUB_TITLE', 'Module')}", expanded=True):
                st.write(f"**Objectives:** {row.get('LEARNING_OBJECTIVES')}")
                c1, c2 = st.columns(2)
                f_links = str(row.get('FILE_LINK', '')).split(", ")
                for i, link in enumerate(f_links):
                    if link: c1.link_button(f"📄 Resource {i+1}", link, use_container_width=True)
                if row.get('VIDEO_LINK'):
                    c2.link_button("🎥 Watch Video", row.get('VIDEO_LINK'), use_container_width=True)
                
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic")
                
                st.write(row.get('Q_TEXT', 'No question text.'))
                with st.form(key=f"diag_{idx}"):
                    t1 = st.radio("Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    t2 = st.select_slider("Confidence", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Reasoning")
                    t4 = st.select_slider("Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    if st.form_submit_button("Submit"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Logged", "N/A")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("Assessment Recorded!")
    except Exception as e:
        st.error(f"Module Error: {e}")

def render_assignments(school):
    st.header("📝 Group Assignments")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assignments").get_all_records())
        df.columns = [c.strip().upper() for c in df.columns]
        my_tasks = df[df['GROUP'].str.upper() == school.upper()]
        
        if my_tasks.empty:
            st.info("No active assignments.")
        for _, task in my_tasks.iterrows():
            with st.expander(f"📋 {task['TITLE']}"):
                st.write(task['INSTRUCTIONS'])
                if task['FILE_LINK']: st.link_button("📥 Download Material", task['FILE_LINK'])
    except: st.error("Unable to load assignments.")

def render_progress(uid):
    st.header("📈 Growth Tracker")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_logs = logs[logs['User_ID'].astype(str) == str(uid)]
        if not user_logs.empty:
            fig = px.line(user_logs, x="Timestamp", y="Tier_2", title="Confidence Progression", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete a module to start your chart.")
    except: st.error("Progress tracker offline.")

def render_ai_chat():
    st.header("🤖 Socratic Tutor")
    if 'current_topic' not in st.session_state:
        st.warning("Complete a module assessment first.")
        return
    st.info(f"Topic: {st.session_state.current_topic}")
    # Chat logic continues here...
