import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    user = st.session_state.user
    user_school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Modules", "📝 Assignments", "📈 Progress"]
    choice = st.sidebar.radio("Navigate", menu)

    if choice == "🏠 Dashboard":
        st.title("Your Learning Hub")
        st.progress(0.4) # Learning progress indicator
        st.write("### Active Assignments")
        st.info("Check the 'Assignments' tab for new tasks.")

    elif choice == "📚 Modules":
        render_modules(user_school)
    
    elif choice == "📝 Assignments":
        render_assignments(user_school)

    elif choice == "📈 Progress":
        render_progress(user.get('User_ID'))

def render_modules(school):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # KEY FIX: Standardize all columns to Uppercase to prevent KeyErrors
        df.columns = [c.strip().upper() for c in df.columns]
        my_lessons = df[df['GROUP'].str.strip().str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('SUB_TITLE', 'Module')}", expanded=True):
                # Handle multiple links
                links = str(row.get('FILE_LINK', '')).split(", ")
                for i, link in enumerate(links):
                    if link: st.link_button(f"📄 Resource {i+1}", link)
                
                st.subheader("🧪 Diagnostic Question")
                
                st.write(row.get('DIAGNOSTIC_QUESTION', 'No question text.'))
                with st.form(key=f"f_{idx}"):
                    t1 = st.radio("Answer", [row.get('OPTION_A'), row.get('OPTION_B')])
                    t2 = st.select_slider("Confidence", ["Unsure", "Sure", "Very Sure"])
                    if st.form_submit_button("Submit"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, "", "", "Logged", "")
                        st.success("Responses Saved!")
    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_assignments(school):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assignments").get_all_records())
        df.columns = [c.strip().upper() for c in df.columns]
        my_tasks = df[df['GROUP'].str.upper() == school.upper()]
        for _, task in my_tasks.iterrows():
            with st.expander(f"📋 {task['TITLE']}"):
                st.write(task['INSTRUCTIONS'])
                if task['FILE_LINK']: st.link_button("📥 View Material", task['FILE_LINK'])
    except: st.error("Assignments currently offline.")

def render_progress(uid):
    st.header("📈 Your Confidence Growth")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_logs = logs[logs['User_ID'].astype(str) == str(uid)]
        if not user_logs.empty:
            fig = px.line(user_logs, x="Timestamp", y="Tier_2", markers=True)
            st.plotly_chart(fig)
        else: st.info("No data yet.")
    except: st.error("Progress tracker offline.")
