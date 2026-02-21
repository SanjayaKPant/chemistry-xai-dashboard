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
    if 'user' not in st.session_state: return
    user = st.session_state.user
    user_school = str(user.get('Group', 'School B')).strip()
    
    # Navigation Sidebar
    st.sidebar.markdown(f"### 🎓 Student Portal\n**{user.get('Name')}**")
    st.sidebar.caption(f"🏫 {user_school} | ID: {user.get('User_ID')}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "📝 Assignments", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Main Menu", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_learning_path(user_school)
    elif choice == "📝 Assignments":
        render_assignments(user_school)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📈 My Progress":
        render_visual_progress(user.get('User_ID'))

def render_dashboard(user):
    st.title(f"Welcome to your Chemistry Hub, {user.get('Name')}! 🧪")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Completed Modules", "0") # Replace with dynamic count
    with c2: st.metric("Current Confidence", "N/A")
    with c3: st.metric("Pending Tasks", "2")

def render_learning_path(school):
    st.subheader("📚 Digital Learning Library")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        data = ws.get_all_values()
        
        if len(data) < 2:
            st.info("No lessons have been deployed yet.")
            return

        df = pd.DataFrame(data[1:], columns=data[0])
        # Filter for student group
        my_data = df[df['Group'].str.strip().str.upper() == school.upper()]

        for idx, row in my_data.iterrows():
            with st.expander(f"🔹 {row['Sub_Title']}", expanded=True):
                # 1. Objectives
                st.info(f"🎯 **Objectives:** {row['Learning_Objectives']}")
                
                # 2. Attachments & Resources (TOP PART)
                st.markdown("#### 📥 Lesson Resources")
                col_a, col_b = st.columns(2)
                with col_a:
                    if row['File_Links']: st.link_button("📄 Open Textbook PDF", row['File_Links'], use_container_width=True)
                with col_b:
                    if row['Video_Links']: st.link_button("🎥 Watch Video Lesson", row['Video_Links'], use_container_width=True)
                
                st.markdown("---")
                
                # 3. 4-Tier Assessment
                st.markdown(f"#### ❓ Diagnostic Question")
                st.write(row['Diagnostic_Question'])
                
                with st.form(key=f"diag_form_{idx}"):
                    t1 = st.radio("Tier 1: Select correct option", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']])
                    t2 = st.select_slider("Tier 2: Confidence in Answer", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Tier 3: Reasoning (Scientific Justification)", placeholder="Explain why you chose this...")
                    t4 = st.select_slider("Tier 4: Confidence in Reasoning", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Start AI Tutoring"):
                        log_assessment(st.session_state.user['User_ID'], school, row['Sub_Title'], t1, t2, t3, t4, "Logged", "N/A")
                        st.session_state.last_justification = t3
                        st.session_state.current_sub = row['Sub_Title']
                        st.success("Success! Now open the '🤖 Socratic Tutor' tab to discuss.")

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_visual_progress(uid):
    st.subheader("📈 Your Personal Learning Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df_logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_logs = df_logs[df_logs['User_ID'].astype(str) == str(uid)]
        
        if not user_logs.empty:
            # Indicator Line (Confidence Tracker)
            fig = px.line(user_logs, x="Timestamp", y="Tier_2", title="Confidence Progression", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Module Mastery Bar
            mastery = user_logs['Module_ID'].value_counts().reset_index()
            fig_bar = px.bar(mastery, x='Module_ID', y='count', title="Activity per Topic")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Complete an assessment to see your progress graph!")
    except:
        st.error("Progress data sheet not found.")

def render_assignments(school):
    st.subheader("📝 Assignment List")
    st.info("The assignments below are assigned to your group.")
    # Placeholder for assignment logic
    st.write("1. 🧪 Modern Periodic Law Worksheet - **Due Friday**")
    st.write("2. 📊 Electronic Configuration Lab Report - **Due Monday**")
