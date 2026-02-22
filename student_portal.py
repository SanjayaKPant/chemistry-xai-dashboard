import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "📝 Assignments", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        st.title(f"Welcome, {user.get('Name')}")
        st.progress(0.4)
        st.info("Complete modules to unlock your Socratic AI Tutor.")

    elif choice == "📚 Learning Modules":
        render_modules(school)

    elif choice == "📝 Assignments":
        render_assignments(school)

    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(school)

    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_modules(school):
    st.header("📚 Digital Lessons")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [c.strip().upper() for c in df.columns]
        
        my_lessons = df[df['GROUP'].str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('SUB_TITLE')}", expanded=True):
                st.write(f"**Objectives:** {row.get('LEARNING_OBJECTIVES')}")
                
                # Resources
                c1, c2 = st.columns(2)
                links = str(row.get('FILE_LINK', '')).split(", ")
                for i, l in enumerate(links):
                    if l.strip(): c1.link_button(f"📄 Resource {i+1}", l.strip())
                if row.get('VIDEO_LINK'): c2.link_button("🎥 Watch Lesson", row.get('VIDEO_LINK'))
                
                # --- 4-TIER DIAGNOSTIC ---
                
                st.subheader("🧪 Misconception Check")
                st.write(row.get('Q_TEXT'))
                with st.form(key=f"f_{idx}"):
                    t1 = st.radio("Tier 1: Your Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    t2 = st.select_slider("Tier 2: Confidence in Answer", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Tier 3: Provide Scientific Reasoning")
                    t4 = st.select_slider("Tier 4: Confidence in Reasoning", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit Assessment"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("Responses recorded! AI Tutor is now active.")
    except Exception as e: st.error(f"Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("AI Tutor is currently in Experimental Phase for Group A.")
        return
    if 'current_topic' not in st.session_state:
        st.info("Submit a module assessment first to provide context to the AI.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # GEMINI LINKING
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        context = f"Topic: {st.session_state.current_topic}. Socratic Plan: {st.session_state.logic_tree}. Student: {prompt}."
        
        response = model.generate_content(context)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

def render_progress(uid):
    st.header("📈 My Progress")
    try:
        df = pd.DataFrame(get_gspread_client().open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60").worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Tracker", markers=True))
        else: st.info("No data yet.")
    except: st.error("Progress engine offline.")

def render_assignments(school):
    st.header("📝 Assignments")
    try:
        df = pd.DataFrame(get_gspread_client().open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60").worksheet("Assignments").get_all_records())
        tasks = df[df['Group'].str.upper() == school.upper()]
        for _, t in tasks.iterrows():
            with st.expander(f"📋 {t['Title']}"):
                st.write(t['Instructions'])
                if t['File_Link']: st.link_button("📥 Download", t['File_Link'])
    except: st.info("No assignments yet.")
