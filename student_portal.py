import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    user = st.session_state.user
    user_school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.markdown(f"## 🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic AI Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigate", menu)

    if choice == "🏠 Dashboard":
        st.title("Welcome to Chemistry Hub")
        st.progress(0.4) # Visual Progress Indicator
        st.write("### 📝 Assignments")
        st.info("Check 'Learning Modules' for new tasks.")

    elif choice == "📚 Learning Modules":
        render_modules(user_school)

    elif choice == "🤖 Socratic AI Tutor":
        render_ai_chat()

    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_modules(school):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        # Load Materials
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # --- KEY FIX: Standardize column names to Uppercase ---
        df.columns = [c.strip().upper() for c in df.columns]
        
        my_lessons = df[df['GROUP'].str.strip().str.upper() == school.upper()]

        if my_lessons.empty:
            st.warning(f"No lessons found for {school}")
            return

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('SUB_TITLE', 'Module')}", expanded=True):
                # Learning Assets at top
                c1, c2 = st.columns(2)
                with c1:
                    f_link = row.get('FILE_LINKS', '')
                    if f_link: st.link_button("📄 Open PDF/Image", f_link, use_container_width=True)
                with c2:
                    v_link = row.get('VIDEO_LINKS', '')
                    if v_link: st.link_button("🎥 Watch Video", v_link, use_container_width=True)
                
                # 4-Tier Assessment
                st.subheader("🧪 Diagnostic Question")
                st.write(row.get('DIAGNOSTIC_QUESTION', 'No question provided.'))
                with st.form(key=f"diag_{idx}"):
                    t1 = st.radio("Answer", [row.get('OPTION_A'), row.get('OPTION_B'), row.get('OPTION_C'), row.get('OPTION_D')])
                    t2 = st.select_slider("Confidence", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Reasoning")
                    t4 = st.select_slider("Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Logged", "N/A")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("Submitted! Unlock the AI Tutor now.")

    except Exception as e:
        st.error(f"Display Error: {e}")

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
            st.info("Complete a module to start your progress chart.")
    except:
        st.error("Progress data offline.")

def render_ai_chat():
    st.header("🤖 Socratic Tutor")
    if 'current_topic' not in st.session_state:
        st.warning("Please finish a module first.")
        return
    st.write(f"Discussing: {st.session_state.current_topic}")
    # (Existing chat logic here...)
