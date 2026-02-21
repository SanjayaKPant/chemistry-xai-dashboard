import streamlit as st
import pandas as pd
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
import plotly.express as px

# --- RESEARCH-GRADE SOCRATIC SYSTEM PROMPT ---
SOCRATIC_PROMPT = """
You are a Socratic Chemistry Tutor designed for Grade 10 students in Nepal. 
Your goal is to guide students toward conceptual clarity using the National Curriculum standards.

SCIENTIFIC APPROACH:
1. Ground questions in molecular behavior, periodic trends (Modern Periodic Law), and sub-shell electronic configuration (Aufbau's Principle).
2. Address specific textbook concepts: Metals/Non-metals, Alkali/Alkaline Earth metals, and Halogens.
3. Scaffolding: Use the 'Socratic_Tree' guidance from the teacher to identify logical hurdles.

ETHICAL GUIDELINES:
- Never provide the final answer or chemical formulas directly.
- Use encouraging language to reduce 'Science Anxiety'.
"""

def show():
    user = st.session_state.user
    user_school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.markdown(f"## 🎓 {user.get('Name')}")
    st.sidebar.info(f"Group: {user_school}")
    
    menu = ["🏠 Dashboard", "📚 Learning Path", "📊 My Progress", "📝 Assignments"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        st.title("Chemistry Hub Dashboard")
        st.subheader("🏁 Learning Progress Indicator")
        # Logic: Compare Assessment_Logs with Instructional_Materials count
        st.progress(0.4) # Placeholder for 40%
        st.caption("Keep going! You are almost halfway through this unit.")
        
    elif choice == "📚 Learning Path":
        render_learning_path(user_school)
        
    elif choice == "📊 My Progress":
        render_progress_chart(user.get('User_ID'))

    elif choice == "📝 Assignments":
        st.header("📝 Assigned Tasks")
        st.write("- [ ] Modern Periodic Table Quiz (Feb 25)")
        st.write("- [ ] Sub-shell configuration exercise (Feb 28)")

def render_learning_path(school):
    st.header("📚 Digital Lessons")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Standardize headers to handle Group vs GROUP
        df.columns = [c.strip().upper() for c in df.columns]
        my_lessons = df[df['GROUP'].str.strip().str.upper() == school.upper()]

        for _, row in my_lessons.iterrows():
            with st.expander(f"📖 {row['SUB_TITLE']}", expanded=True):
                st.info(f"🎯 **Objective:** {row['LEARNING_OBJECTIVES']}")
                
                # RESOURCES AT THE TOP
                col1, col2 = st.columns(2)
                with col1:
                    if row['FILE_LINKS']: st.link_button("📄 Open PDF Context", row['FILE_LINKS'], use_container_width=True)
                with col2:
                    if row['VIDEO_LINKS']: st.link_button("🎥 Watch Lesson", row['VIDEO_LINKS'], use_container_width=True)
                
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic Assessment")
                st.write(row['DIAGNOSTIC_QUESTION'])
                
                with st.form(key=f"form_{row['SUB_TITLE']}"):
                    t1 = st.radio("Select Answer", [row['OPTION_A'], row['OPTION_B'], row['OPTION_C'], row['OPTION_D']])
                    t2 = st.select_slider("Confidence in Answer", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Provide your Reasoning")
                    t4 = st.select_slider("Confidence in Reasoning", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit Assessment"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Logged", "N/A")
                        st.success("Responses recorded! Check your progress tab.")
    except Exception as e:
        st.error(f"Error: {e}")

def render_progress_chart(uid):
    st.header("📈 My Confidence Growth")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_logs = logs[logs['User_ID'].astype(str) == str(uid)]
        if not user_logs.empty:
            fig = px.line(user_logs, x="Timestamp", y="Tier_2", title="Confidence Level Progression", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete a lesson to see your progress data.")
    except:
        st.error("Progress data unavailable.")
