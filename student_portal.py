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
    st.sidebar.info(f"Group: {student_group}")
    
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
    st.info(f"Welcome! You are currently viewing modules for **{group}**.")
    # Add a visual reminder of the 4-tier process
    

def render_modules(student_group):
    st.header("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        df = pd.DataFrame(ws.get_all_records())

        if df.empty:
            st.warning("No data found in the sheet.")
            return

        # --- EXACT MAPPING TO YOUR GOOGLE SHEET ---
        # We filter where the 'Group' column matches the student's group
        my_lessons = df[df['Group'].str.strip() == student_group]

        if my_lessons.empty:
            st.error(f"No modules assigned to {student_group} yet.")
            st.write("Teacher has assigned modules to:", df['Group'].unique().tolist())
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.subheader(f"📖 {row.get('Main_Title')}")
                st.markdown(f"**Topic:** {row.get('Sub_Title')}")
                
                # 1. INSTRUCTIONAL LINKS (PDF & VIDEO)
                st.markdown("### 📦 Learning Materials")
                c1, c2 = st.columns(2)
                
                # Match: 'File_Links (PDF/Images)'
                pdf_link = str(row.get('File_Links (PDF/Images)', '')).strip()
                if pdf_link.startswith("http"):
                    c1.link_button("📂 View Study PDF", pdf_link, use_container_width=True)
                
                # Match: 'Video_Links'
                vid_link = str(row.get('Video_Links', '')).strip()
                if vid_link.startswith("http"):
                    c2.video(vid_link)

                # 2. 4-TIER QUESTION
                st.divider()
                st.markdown("### 🧪 Diagnostic Question")
                
                # Match: 'Diagnostic_Question'
                question_body = row.get('Diagnostic_Question', 'Question text missing')
                st.info(question_body)
                
                with st.form(key=f"tier_form_{idx}"):
                    # Match: Option_A, Option_B, etc.
                    opts = [row.get('Option_A'), row.get('Option_B'), row.get('Option_C'), row.get('Option_D')]
                    opts = [o for o in opts if o] # Clean empty options
                    
                    col_a, col_b = st.columns(2)
                    t1 = col_a.radio("Tier 1: Select Answer", opts)
                    t2 = col_b.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    t3 = st.text_area("Tier 3: Reasoning (Explain your choice)")
                    t4 = st.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock Tutor"):
                        log_assessment(st.session_state.user['User_ID'], student_group, row.get('Sub_Title'), t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = row.get('Sub_Title')
                        st.session_state.logic_tree = row.get('Socratic_Tree')
                        st.success("✅ Logged! Now go to the Socratic Tutor tab.")

    except Exception as e:
        st.error(f"Error reading Sheet: {e}")

# ... (rest of functions remain unchanged)

def render_ai_chat(school):
    if "School A" not in school:
        st.warning("AI Tutor is for Experimental Group only.")
        return
    if 'current_topic' not in st.session_state:
        st.info("Complete a module quiz first.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        context = f"Topic: {st.session_state.current_topic}. Teacher Logic: {st.session_state.logic_tree}. Student input: {prompt}."
        
        response = model.generate_content(context)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

def render_progress(uid):
    st.header("📈 Growth Timeline")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", markers=True))
    except: st.error("Analytics offline.")
