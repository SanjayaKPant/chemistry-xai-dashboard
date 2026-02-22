import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    st.markdown("""
        <style>
        .metric-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; text-align: center; }
        .instruction-container { background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; margin-bottom: 20px; }
        .sub-title-text { color: #555; font-size: 1.2rem; font-style: italic; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "📝 Assignments", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user, school)
    elif choice == "📚 Learning Modules":
        render_modules(school)
    elif choice == "📝 Assignments":
        render_assignments(school)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(school)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user, school):
    st.title(f"🚀 Student Command Center")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><h3>Group</h3><p>{school}</p></div>', unsafe_allow_html=True)
    with m2: st.markdown('<div class="metric-card"><h3>Status</h3><p>Active</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Goal</h3><p>Mastery</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Level</h3><p>Grade 10</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📢 Daily Announcements")
        st.info("💡 **Pro-Tip:** Check the 'Video Lessons' in your modules before attempting the 4-Tier Diagnostic.")
    with c2:
        st.subheader("📊 Your Progress")
        st.progress(0.4)
        st.caption("Overall Course Completion: 40%")

def render_modules(school):
    st.header("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [c.strip().upper() for c in df.columns]
        
        my_lessons = df[df['GROUP'].str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.write(f"### {row.get('MAIN_TITLE')}")
                st.markdown(f"<div class='sub-title-text'>Topic: {row.get('SUB_TITLE')}</div>", unsafe_allow_html=True)
                st.write(f"**Objectives:** {row.get('LEARNING_OBJECTIVES')}")

                # SECTION 1: INSTRUCTIONAL MATERIALS (Above the Diagnostic)
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📦 Instructional Resources")
                col_file, col_vid = st.columns([1, 1])
                with col_file:
                    st.write("**📄 Lecture Notes & PPTs**")
                    links = str(row.get('FILE_LINK', '')).split(", ")
                    for i, link in enumerate(links):
                        if link.strip(): st.link_button(f"Open Resource {i+1}", link.strip(), use_container_width=True)
                with col_vid:
                    st.write("**🎥 Video Lessons**")
                    if row.get('VIDEO_LINK'): st.video(row.get('VIDEO_LINK'))
                    else: st.caption("No video resource provided.")
                st.markdown('</div>', unsafe_allow_html=True)

                # SECTION 2: COMPACT 4-TIER DIAGNOSTIC
                st.markdown("---")
                st.subheader("🧪 4-Tier Concept Check")
                
                st.write(f"**Diagnostic Question:** {row.get('Q_TEXT')}")
                
                with st.form(key=f"form_{idx}"):
                    r1_c1, r1_c2 = st.columns(2)
                    t1 = r1_c1.radio("Tier 1: Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    t2 = r1_c2.select_slider("Tier 2: Confidence", ["Low", "Medium", "High"])
                    
                    r2_c1, r2_c2 = st.columns([2, 1])
                    t3 = r2_c1.text_area("Tier 3: Scientific Reasoning (Explain)")
                    t4 = r2_c2.select_slider("Tier 4: Reason Confidence", ["Low", "Medium", "High"])
                    
                    if st.form_submit_button("Submit & Unlock AI Tutor"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("✅ Assessment Recorded! Open the 'Socratic Tutor' tab to discuss.")
                        log_temporal_trace(st.session_state.user['User_ID'], "MODULE_SUBMIT", row['SUB_TITLE'])
    except Exception as e: st.error(f"Module Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("AI features are currently available for Experimental Group A.")
        return
    if 'current_topic' not in st.session_state:
        st.info("👋 Please finish a diagnostic question in 'Learning Modules' first.")
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
        context = f"Topic: {st.session_state.current_topic}. Teacher's Logic: {st.session_state.logic_tree}. Student input: {prompt}."
        
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
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Tracker", markers=True))
        else: st.info("No data yet.")
    except: st.error("Progress engine offline.")

def render_assignments(school):
    st.header("📝 Assignments")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assignments").get_all_records())
        tasks = df[df['Group'].str.upper() == school.upper()]
        for _, t in tasks.iterrows():
            with st.expander(f"📋 {t['Title']}"):
                st.write(t['Instructions'])
                if t['File_Link']: st.link_button("📥 Download Resource", t['File_Link'])
    except: st.info("No assignments yet.")
