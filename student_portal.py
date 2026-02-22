import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

# AI Setup
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')

def show():
    user = st.session_state.user
    user_school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.markdown(f"### 🎓 {user.get('Name')}")
    st.sidebar.caption(f"ID: {user.get('User_ID')} | Group: {user_school}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "📝 Assignments", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard()
    elif choice == "📚 Learning Modules":
        render_modules(user_school)
    elif choice == "📝 Assignments":
        render_assignments(user_school)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(user_school)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard():
    st.title("Chemistry Learning Hub")
    st.subheader("Your Progress Tracker")
    st.progress(0.4)
    st.markdown("""
    Welcome! Explore your modules, complete diagnostic assessments, 
    and use the Socratic Tutor to master complex chemistry concepts.
    """)

def render_modules(school):
    st.header("📚 Digital Lessons")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # --- FIX: HEADER NORMALIZATION ---
        df.columns = [c.strip().upper() for c in df.columns]
        my_lessons = df[df['GROUP'].str.strip().str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('SUB_TITLE', 'Module')}", expanded=True):
                st.info(f"🎯 **Objective:** {row.get('LEARNING_OBJECTIVES')}")
                
                # Resources Row
                c1, c2 = st.columns(2)
                f_links = str(row.get('FILE_LINK', '')).split(", ")
                for i, link in enumerate(f_links):
                    if link: c1.link_button(f"📄 Resource {i+1}", link.strip(), use_container_width=True)
                if row.get('VIDEO_LINK'):
                    c2.link_button("🎥 Watch Lesson", row.get('VIDEO_LINK'), use_container_width=True)
                
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic Assessment")
                
                st.write(row.get('Q_TEXT', "No question available."))
                
                with st.form(key=f"diag_{idx}"):
                    t1 = st.radio("Select Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    t2 = st.select_slider("Confidence in Answer", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Scientific Reasoning")
                    t4 = st.select_slider("Confidence in Reasoning", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit Assessment"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Logged", "N/A")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("Responses recorded! You can now use the AI Tutor.")

    except Exception as e:
        st.error(f"Module Loading Error: {e}")

def render_assignments(school):
    st.header("📝 Task List")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assignments").get_all_records())
        df.columns = [c.strip().upper() for c in df.columns]
        my_tasks = df[df['GROUP'].str.upper() == school.upper()]
        
        if my_tasks.empty:
            st.info("No assignments currently posted for your group.")
        for _, task in my_tasks.iterrows():
            with st.expander(f"📋 {task['TITLE']}"):
                st.write(task['INSTRUCTIONS'])
                if task['FILE_LINK']: st.link_button("📥 View Assignment File", task['FILE_LINK'])
    except:
        st.error("Assignment list offline.")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The AI Tutor is currently in Experimental Phase for Group A only.")
        return
    
    if 'current_topic' not in st.session_state:
        st.warning("Please complete a Diagnostic Question first to provide context for the AI.")
        return

    st.header("🤖 Socratic Tutor")
    topic = st.session_state.current_topic
    tree = st.session_state.logic_tree
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"I've reviewed your thoughts on {topic}. Let's dive deeper—why do you think that specific chemical property applies here?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        context = f"Topic: {topic}. Teacher Plan: {tree}. Student Input: {prompt}."
        response = model.generate_content(context)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        log_temporal_trace(st.session_state.user['User_ID'], "AI_CHAT", topic)

def render_progress(uid):
    st.header("📈 My Learning Journey")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_logs = logs[logs['User_ID'].astype(str) == str(uid)]
        if not user_logs.empty:
            fig = px.line(user_logs, x="Timestamp", y="Tier_2", title="Confidence Progression", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet. Complete an assessment to see your chart.")
    except:
        st.error("Progress tracker offline.")
