import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

# Initialize Gemini
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')

def show():
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    # RESTORED MENU
    menu = ["🏠 Dashboard", "📚 Learning Modules", "📝 Assignments", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        st.title("Chemistry Learning Portal")
        st.progress(0.4)
        st.info("Check 'Learning Modules' to start your diagnostic tests.")

    elif choice == "📚 Learning Modules":
        render_modules(school)

    elif choice == "📝 Assignments":
        render_assignments(school)

    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(school)

    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_modules(school):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [c.strip().upper() for c in df.columns] # NORMALIZE HEADERS
        
        my_lessons = df[df['GROUP'].str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('SUB_TITLE')}", expanded=True):
                st.write(f"**Objectives:** {row.get('LEARNING_OBJECTIVES')}")
                
                # RESTORED RESOURCES
                c1, c2 = st.columns(2)
                links = str(row.get('FILE_LINK', '')).split(", ")
                for i, l in enumerate(links):
                    if l: c1.link_button(f"📄 Material {i+1}", l.strip())
                if row.get('VIDEO_LINK'): c2.link_button("🎥 Watch Lesson", row.get('VIDEO_LINK'))
                
                # RESTORED 4-TIER ASSESSMENT
                
                st.subheader("🧪 4-Tier Diagnostic")
                st.write(row.get('Q_TEXT'))
                with st.form(key=f"f_{idx}"):
                    ans = st.radio("Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    conf1 = st.select_slider("Answer Confidence", ["Unsure", "Sure", "Very Sure"])
                    reason = st.text_area("Scientific Reasoning")
                    conf2 = st.select_slider("Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock AI"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], ans, conf1, reason, conf2, "Logged", "")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("Unlocked! Go to Socratic Tutor.")
    except Exception as e: st.error(f"Module error: {e}")

def render_progress(uid):
    st.header("📈 Growth Timeline")
    try:
        df = pd.DataFrame(get_gspread_client().open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60").worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", markers=True))
        else: st.info("Complete a module to see progress.")
    except: st.error("Tracker offline.")

def render_ai_chat(school):
    if school != "School A": st.warning("AI Tutor for School A only."); return
    if 'current_topic' not in st.session_state: st.warning("Complete a Diagnostic first."); return
    st.header(f"🤖 Tutor: {st.session_state.current_topic}")
    # Chat logic here...
