import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

# CSS for a Modern Student UI
st.markdown("""
    <style>
    .module-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 15px; }
    .stProgress > div > div > div > div { background-color: #007bff; }
    .sidebar-info { font-size: 12px; color: #666; }
    </style>
""", unsafe_allow_html=True)

def show():
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.markdown(f"<p class='sidebar-info'>ID: {user.get('User_ID')} | Group: {school}</p>", unsafe_allow_html=True)
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "📝 Assignments", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(school)
    elif choice == "📝 Assignments":
        render_assignments(school)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(school)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user):
    st.title(f"Welcome Back, {user.get('Name')}!")
    st.subheader("Current Learning Milestone")
    st.progress(0.4)
    st.info("💡 Pro-Tip: Submit your Diagnostic questions in 'Learning Modules' to unlock the Socratic AI Chat.")

def render_modules(school):
    st.header("📚 Digital Library")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [c.strip().upper() for c in df.columns]
        
        my_lessons = df[df['GROUP'].str.upper() == school.upper()]

        if my_lessons.empty:
            st.warning("No modules deployed for your group yet.")
            return

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('SUB_TITLE', 'Module')}", expanded=True):
                st.markdown(f"**Objectives:** {row.get('LEARNING_OBJECTIVES')}")
                
                # Resources Section
                c1, c2 = st.columns(2)
                f_links = str(row.get('FILE_LINK', '')).split(", ")
                for i, l in enumerate(f_links):
                    if l: c1.link_button(f"📄 View Resource {i+1}", l.strip(), use_container_width=True)
                if row.get('VIDEO_LINK'):
                    c2.link_button("🎥 Watch Lesson", row.get('VIDEO_LINK'), use_container_width=True)

                st.markdown("---")
                st.subheader("🧪 Diagnostic Assessment")
                st.write(row.get('Q_TEXT'))
                
                # --- 4-TIER DIAGNOSTIC FORM ---
                with st.form(key=f"diag_{idx}"):
                    t1 = st.radio("Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')], key=f"t1_{idx}")
                    t2 = st.select_slider("How sure are you about this answer?", ["Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                    t3 = st.text_area("What is the scientific reason for your choice?", key=f"t3_{idx}")
                    t4 = st.select_slider("How sure are you about your reasoning?", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                    
                    if st.form_submit_button("Submit & Sync with AI"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Complete", "N/A")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("Data synced! AI Tutor is now ready.")
    except Exception as e:
        st.error(f"Module Engineering Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The Socratic AI is currently enabled for Experimental Group A only.")
        return
    
    if 'current_topic' not in st.session_state:
        st.error("Please complete the Diagnostic Question in 'Learning Modules' first.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # LINKING GEMINI
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        context = f"Topic: {st.session_state.current_topic}. Teacher's Logic Tree: {st.session_state.logic_tree}. Student input: {prompt}."
        response = model.generate_content(context)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

def render_progress(uid):
    st.header("📈 My Progress Tracker")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        
        if not user_df.empty:
            fig = px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Growth Over Time", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Finish your first module to see your progress chart!")
    except:
        st.error("Progress engine offline.")

def render_assignments(school):
    st.header("📝 Task List")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assignments").get_all_records())
        my_tasks = df[df['Group'].str.upper() == school.upper()]
        
        if my_tasks.empty:
            st.info("No active assignments for your group.")
        else:
            for _, task in my_tasks.iterrows():
                with st.expander(f"📋 {task['Title']}"):
                    st.write(task['Instructions'])
                    if task['File_Link']: st.link_button("📥 Download", task['File_Link'])
    except:
        st.error("Assignment list offline.")
