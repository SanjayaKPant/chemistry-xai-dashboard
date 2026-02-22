import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {student_group}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user, student_group)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user, group):
    st.title(f"🚀 Student Command Center")
    st.info(f"Welcome, Scientist. You are in the **{group}** study group.")
    st.success("Navigate to 'Learning Modules' to begin your assignment.")

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        df = pd.DataFrame(ws.get_all_records())
        my_lessons = df[df['Group'].str.strip() == student_group]

        if my_lessons.empty:
            st.warning(f"No modules assigned to {student_group}.")
            return

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('Sub_Title')}", expanded=True):
                col1, col2 = st.columns(2)
                f_link = str(row.get('File_Links (PDF/Images)', '')).strip()
                if f_link.startswith("http"):
                    col1.link_button("📂 View Chapter PDF", f_link, use_container_width=True)
                v_link = str(row.get('Video_Links', '')).strip()
                if v_link.startswith("http"):
                    col2.video(v_link)

                st.divider()
                st.subheader("🧪 4-Tier Diagnostic Check")
                st.markdown(f"**Question:** {row.get('Diagnostic_Question')}")
                
                with st.form(key=f"eval_{idx}"):
                    opts = [row.get('Option_A'), row.get('Option_B'), row.get('Option_C'), row.get('Option_D')]
                    opts = [str(o) for o in opts if o and str(o).strip()]
                    c1, c2 = st.columns(2)
                    t1 = c1.radio("Tier 1: Answer", opts if opts else ["Options Missing"])
                    t2 = c2.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"])
