import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    # CSS for the High-Density Professional Dashboard
    st.markdown("""
        <style>
        .metric-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; text-align: center; }
        .instruction-container { background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; margin-bottom: 20px; }
        .sub-title-text { color: #007bff; font-weight: bold; font-size: 1.3rem; margin-bottom: 5px;}
        .objective-text { color: #555; font-style: italic; margin-bottom: 15px; display: block; }
        .question-box { background: #fffdf0; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin-top: 10px; font-weight: 500; }
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
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><h3>Group</h3><p>{school}</p></div>', unsafe_allow_html=True)
    with m2: st.markdown('<div class="metric-card"><h3>Course</h3><p>Chemistry 10</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Status</h3><p>Active</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Task</h3><p>Diagnostic</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📢 Teacher's Updates")
        st.info("💡 **Welcome!** Please visit 'Learning Modules' to access your instructional videos and PDFs. Complete the quiz to unlock the AI Tutor.")
    with c2:
        st.subheader("📊 Course Progress")
        st.progress(0.4)
        st.caption("Overall Mastery: 40%")

def render_modules(school):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        
        # --- SMART MAPPING LAYER ---
        df = pd.DataFrame(data[1:], columns=data[0])
        # Force all column headers to be lowercase and no spaces for reliable lookups
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        # Filtering for the correct group
        my_lessons = df[df['group'].str.upper() == school.upper()]

        if my_lessons.empty:
            st.warning("No materials have been deployed for your group yet.")
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.markdown(f"## {row.get('main_title', row.get('chapter_(main_title)', 'Module'))}")
                st.markdown(f"<div class='sub-title-text'>{row.get('sub_title', row.get('concept_(sub_title)', 'Topic'))}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='objective-text'>🎯 {row.get('objectives', 'Standard Learning Objective')}</span>", unsafe_allow_html=True)

                # --- 1. INSTRUCTIONAL MATERIALS (PDF & VIDEO) ---
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📖 Lesson Resources")
                col_file, col_vid = st.columns([1, 1.2])
                
                with col_file:
                    st.write("**📄 Reference Materials**")
                    raw_links = str(row.get('file_link', '')).split(", ")
                    valid_links = [l.strip() for l in raw_links if l.strip().startswith("http")]
                    if valid_links:
                        for i, link in enumerate(valid_links):
                            st.link_button(f"📥 Open PDF {i+1}", link, use_container_width=True)
                    else:
                        st.caption("No PDFs available.")

                with col_vid:
                    st.write("**🎥 Video Lesson**")
                    vid_url = str(row.get('video_link', '')).strip()
                    if vid_url.startswith("http"):
                        st.video(vid_url)
                    else:
                        st.info("No video provided.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- 2. THE 4-TIER DIAGNOSTIC GRID ---
                st.markdown("---")
                st.subheader("🧪 4-Tier Concept Check")
                
                
                
                q_text = row.get('q_text', row.get('question_text', 'No question content found.'))
                st.markdown(f"<div class='question-box'>Q: {q_text}</div>", unsafe_allow_html=True)
                
                with st.form(key=f"diag_form_{idx}"):
                    # ROW 1: T1 & T2
                    r1c1, r1c2 = st.columns(2)
                    opts = [row.get('oa'), row.get('ob'), row.get('oc'), row.get('od')]
                    opts = [o for o in opts if o] # Remove empty slots
                    
                    t1 = r1c1.radio("Tier 1: Answer Choice", opts)
                    t2 = r1c2.select_slider("Tier 2: Confidence in Answer", ["Unsure", "Sure", "Very Sure"])
                    
                    # ROW 2: T3 & T4
                    r2c1, r2c2 = st.columns([2, 1])
                    t3 = r2c1.text_area("Tier 3: Reasoning (Why did you choose this?)")
                    t4 = r2c2.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock AI Tutor"):
                        t_id = row.get('sub_title', row.get('concept_(sub_title)', 'Unknown'))
                        log_assessment(st.session_state.user['User_ID'], school, t_id, t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = t_id
                        st.session_state.logic_tree = row.get('socratic_tree', '')
                        st.success(f"✅ Assessment Saved! Unlock the AI Tutor for {t_id}.")
                        log_temporal_trace(st.session_state.user['User_ID'], "SUBMITTED_DIAGNOSTIC", t_id)

    except Exception as e:
        st.error(f"Display Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The AI Tutor is currently enabled for Group A only.")
        return
    if 'current_topic' not in st.session_state:
        st.info("👋 Please complete a diagnostic question in 'Learning Modules' first.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Tell me more about your reasoning..."):
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
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Tracker", markers=True))
        else: st.info("Finish your first module to see your chart!")
    except: st.error("Progress engine offline.")
