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
        .sub-title-text { color: #007bff; font-weight: bold; font-size: 1.3rem; }
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
    st.title(f"🚀 Student Command Center")
    
    # ROW 1: Filling Whitespace with Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><h3>Group</h3><p>{school}</p></div>', unsafe_allow_html=True)
    with m2: st.markdown('<div class="metric-card"><h3>Course</h3><p>Chemistry X</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Status</h3><p>On Track</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Modules</h3><p>Active</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📢 Recent Announcements")
        st.info("💡 **From your Teacher:** Review the sub-shell configuration PDF before attempting the diagnostic quiz today.")
    with c2:
        st.subheader("📊 Your Progress")
        st.progress(0.4)
        st.caption("Completion: 40%")

def render_modules(school):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [c.strip().upper() for c in df.columns]
        
        my_lessons = df[df['GROUP'].str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.markdown(f"## {row.get('MAIN_TITLE')}")
                st.markdown(f"<div class='sub-title-text'>{row.get('SUB_TITLE')}</div>", unsafe_allow_html=True)
                st.write(f"**Objectives:** {row.get('LEARNING_OBJECTIVES')}")

                # --- STEP 1: DEDICATED INSTRUCTIONAL SPACE (ABOVE THE QUESTION) ---
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📦 Lesson Resources")
                col_file, col_vid = st.columns([1, 1.2])
                with col_file:
                    st.write("**📄 Downloads**")
                    links = str(row.get('FILE_LINK', '')).split(", ")
                    for i, link in enumerate(links):
                        if link.strip(): st.link_button(f"Resource {i+1}", link.strip(), use_container_width=True)
                with col_vid:
                    st.write("**🎥 Video Lesson**")
                    if row.get('VIDEO_LINK'): st.video(row.get('VIDEO_LINK'))
                    else: st.caption("No video resource available.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- STEP 2: COMPACT 4-TIER GRID ---
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic Check")
                
                st.write(f"**Question:** {row.get('Q_TEXT')}")
                
                with st.form(key=f"diag_{idx}"):
                    # Compressed Row 1
                    r1_c1, r1_c2 = st.columns(2)
                    t1 = r1_c1.radio("Tier 1: Select Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    t2 = r1_c2.select_slider("Tier 2: Confidence level", ["Unsure", "Sure", "Very Sure"])
                    
                    # Compressed Row 2
                    r2_c1, r2_c2 = st.columns([2, 1])
                    t3 = r2_c1.text_area("Tier 3: Reasoning (Why did you choose this?)")
                    t4 = r2_c2.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock Socratic AI"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Submitted", "")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("✅ Assessment Saved! You can now use the Socratic Tutor for help.")
                        log_temporal_trace(st.session_state.user['User_ID'], "SUBMIT_MODULE", row['SUB_TITLE'])

    except Exception as e:
        st.error(f"Module Loading Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The AI Tutor is currently in experimental phase for School A.")
        return
    if 'current_topic' not in st.session_state:
        st.info("👋 To start, please complete a Diagnostic Question in the 'Learning Modules' section.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask a follow-up or explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        context = f"Topic: {st.session_state.current_topic}. Teacher Logic: {st.session_state.logic_tree}. Student: {prompt}."
        
        response = model.generate_content(context)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

def render_progress(uid):
    st.header("📈 My Learning Journey")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Tracker", markers=True))
        else: st.info("No data yet. Complete a module to see your growth!")
    except: st.error("Analytics engine currently offline.")
