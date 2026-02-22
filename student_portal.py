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
    st.success("Navigate to 'Learning Modules' to begin your current chemistry assignment.")

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        df = pd.DataFrame(ws.get_all_records())
        my_lessons = df[df['Group'].str.strip() == student_group]

        if my_lessons.empty:
            st.warning(f"No modules assigned to {student_group} yet.")
            return

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('Main_Title')} - {row.get('Sub_Title')}", expanded=True):
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
                    t3 = st.text_area("Tier 3: Reasoning")
                    t4 = st.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock AI"):
                        log_assessment(st.session_state.user['User_ID'], student_group, row.get('Sub_Title'), t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = row.get('Sub_Title')
                        st.session_state.logic_tree = row.get('Socratic_Tree')
                        st.success("✅ Logged!")

    except Exception as e:
        st.error(f"⚠️ System Error: {e}")

def render_ai_chat(school):
    if school not in ["School A", "Exp_A"]:
        st.warning("The Socratic AI Tutor is reserved for the Experimental Group.")
        return
    if 'current_topic' not in st.session_state:
        st.info("👋 Please complete a Diagnostic Check in 'Learning Modules' first.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"AI Setup Error: {e}")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask a follow-up..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        try:
            system_prompt = f"PhD Chemistry Socratic Tutor. Topic: {st.session_state.current_topic}. Goal: {st.session_state.logic_tree}. No answers. Max 3 sentences."
            response = model.generate_content(f"{system_prompt}\nStudent: {prompt}")
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            log_temporal_trace(st.session_state.user['User_ID'], "AI_CHAT", st.session_state.current_topic)
        except Exception as e:
            st.error(f"⚠️ Connection Error: {e}")

def render_progress(uid):
    st.header("📈 My Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            fig = px.line(user_df, x="Timestamps", y="Tier_2 (Confidence_Ans)", title="Confidence Growth", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Analytics updating... {e}")
