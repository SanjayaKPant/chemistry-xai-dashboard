import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    # Professional UI Styling
    st.markdown("""
        <style>
        .metric-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; text-align: center; }
        .instruction-container { background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; margin-bottom: 20px; }
        .sub-title-text { color: #555; font-size: 1.2rem; font-style: italic; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user, school)
    elif choice == "📚 Learning Modules":
        render_modules(school)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(school)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user, school):
    st.title(f"Welcome back, {user.get('Name')}!")
    
    # Professional Metrics to fill whitespace
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown('<div class="metric-card"><h3>Group</h3><p>'+school+'</p></div>', unsafe_allow_html=True)
    with m2: st.markdown('<div class="metric-card"><h3>Status</h3><p>Active</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Goal</h3><p>Mastery</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Level</h3><p>Grade 10</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📢 Daily Pro-Tip")
        st.info("💡 Review the **Sub-shell Configuration** video in the Learning Modules before starting the assessment!")
    with c2:
        st.subheader("📊 Course Progress")
        st.progress(0.4)
        st.caption("40% of Curriculum Completed")

def render_modules(school):
    st.header("📚 Your Learning Curriculum")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [c.strip().upper() for c in df.columns]
        
        my_lessons = df[df['GROUP'].str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.container():
                # Display Sub-title and Learning Objectives
                st.write(f"### {row.get('MAIN_TITLE')}")
                st.markdown(f"<div class='sub-title-text'>Topic: {row.get('SUB_TITLE')}</div>", unsafe_allow_html=True)
                st.write(f"**Learning Objectives:** {row.get('LEARNING_OBJECTIVES')}")

                # SECTION 1: INSTRUCTIONAL MATERIALS (Above the Diagnostic)
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📦 Essential Resources")
                col_file, col_vid = st.columns([1, 1])
                with col_file:
                    st.write("**📄 Study Materials**")
                    links = str(row.get('FILE_LINK', '')).split(", ")
                    for i, link in enumerate(links):
                        if link.strip(): st.link_button(f"Open Material {i+1}", link.strip(), use_container_width=True)
                with col_vid:
                    st.write("**🎥 Video Lecture**")
                    if row.get('VIDEO_LINK'): st.video(row.get('VIDEO_LINK'))
                    else: st.caption("No video available.")
                st.markdown('</div>', unsafe_allow_html=True)

                # SECTION 2: COMPACT 4-TIER DIAGNOSTIC
                st.markdown("---")
                st.subheader("🧪 Concept Check (4-Tier)")
                st.write(f"**Diagnostic Question:** {row.get('Q_TEXT')}")
                
                

                with st.form(key=f"form_{idx}"):
                    r1_c1, r1_c2 = st.columns(2)
                    t1 = r1_c1.radio("Tier 1: Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    t2 = r1_c2.select_slider("Tier 2: Confidence", ["Low", "Medium", "High"])
                    
                    r2_c1, r2_c2 = st.columns([2, 1])
                    t3 = r2_c1.text_area("Tier 3: Scientific Reasoning")
                    t4 = r2_c2.select_slider("Tier 4: Reason Confidence", ["Low", "Medium", "High"])
                    
                    if st.form_submit_button("Submit & Unlock Tutor"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("✅ Results Saved! The Socratic AI Tutor is now ready.")
                        log_temporal_trace(st.session_state.user['User_ID'], "MODULE_SUBMIT", row['SUB_TITLE'])

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The Socratic Tutor is currently available for Group A.")
        return
    if 'current_topic' not in st.session_state:
        st.info("👋 Please finish a diagnostic question in 'Learning Modules' to start your tutoring session.")
        return

    st.header(f"🤖 AI Tutor: {st.session_state.current_topic}")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your thoughts..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        context = f"Topic: {st.session_state.current_topic}. Socratic Logic: {st.session_state.logic_tree}. Student input: {prompt}."
        
        response = model.generate_content(context)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

def render_progress(uid):
    st.header("📈 Growth Tracker")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Progression", markers=True))
        else: st.info("No data yet.")
    except: st.error("Progress engine offline.")
