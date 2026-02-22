import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    # CSS for high-density professional UI
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
    
    # Fill whitespace with key metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><h3>Group</h3><p>{school}</p></div>', unsafe_allow_html=True)
    with m2: st.markdown('<div class="metric-card"><h3>Course</h3><p>Chemistry X</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Status</h3><p>Active</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Task</h3><p>Diagnostic</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📢 Teacher's Guidance")
        st.info("💡 **Welcome, Student!** Pro-tip: Review the instructional materials (PDF/Video) below before submitting your assessment to unlock the Socratic AI Tutor.")
    with c2:
        st.subheader("📊 Course Progress")
        st.progress(0.4)
        st.caption("40% Completion")

def render_modules(school):
    st.header("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        
        # --- DATA NORMALIZATION LAYER ---
        df = pd.DataFrame(data[1:], columns=data[0])
        # Force column names to lowercase and strip spaces to match database_manager.py logic
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        # Filter modules for the student's group
        my_lessons = df[df['group'].str.upper() == school.upper()]

        if my_lessons.empty:
            st.warning("No learning materials have been assigned to your group yet.")
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                # Display Titles & Objectives
                st.markdown(f"## {row.get('main_title', 'Module')}")
                st.markdown(f"<div class='sub-title-text'>{row.get('sub_title', 'Section')}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='objective-text'>🎯 {row.get('objectives', 'Standard objective')}</span>", unsafe_allow_html=True)

                # --- PART 1: INSTRUCTIONAL MATERIALS (TOP SECTION) ---
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📦 Lesson Resources")
                col_file, col_vid = st.columns([1, 1.2])
                
                with col_file:
                    st.write("**📄 Reference Materials**")
                    links = str(row.get('file_link', '')).split(", ")
                    valid_links = [l.strip() for l in links if l.strip().startswith("http")]
                    if valid_links:
                        for i, link in enumerate(valid_links):
                            st.link_button(f"Open Resource {i+1}", link, use_container_width=True)
                    else:
                        st.caption("No PDFs/Files uploaded.")

                with col_vid:
                    st.write("**🎥 Video Lesson**")
                    vid_url = str(row.get('video_link', '')).strip()
                    if vid_url.startswith("http"):
                        st.video(vid_url)
                    else:
                        st.info("No video lecture provided.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- PART 2: COMPACT 4-TIER DIAGNOSTIC ---
                st.markdown("---")
                st.subheader("🧪 Diagnostic Assessment")
                
                # Fetching question from normalized 'q_text'
                q_body = row.get('q_text', 'No question provided.')
                st.markdown(f"<div class='question-box'>Q: {q_body}</div>", unsafe_allow_html=True)
                
                

                with st.form(key=f"eval_{idx}"):
                    # Compressed Grid Layout
                    r1_c1, r1_c2 = st.columns(2)
                    # Mapping options dynamically
                    opts = [row.get('oa'), row.get('ob'), row.get('oc'), row.get('od')]
                    opts = [o for o in opts if o] # Remove empty strings
                    
                    t1 = r1_c1.radio("Tier 1: Answer Choice", opts)
                    t2 = r1_c2.select_slider("Tier 2: Confidence level", ["Unsure", "Sure", "Very Sure"])
                    
                    r2_c1, r2_c2 = st.columns([2, 1])
                    t3 = r2_c1.text_area("Tier 3: Reasoning (Briefly explain your choice)")
                    t4 = r2_c2.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Activate Tutor"):
                        # Use sub_title as the module_id for tracking
                        topic_id = row.get('sub_title', 'Unknown')
                        log_assessment(st.session_state.user['User_ID'], school, topic_id, t1, t2, t3, t4, "Logged", "N/A")
                        
                        # Store session data to unlock Tutor
                        st.session_state.current_topic = topic_id
                        st.session_state.logic_tree = row.get('socratic_tree', '')
                        st.success(f"✅ Success! Socratic Tutor unlocked for {topic_id}.")
                        log_temporal_trace(st.session_state.user['User_ID'], "SUBMITTED_ASSESSMENT", topic_id)

    except Exception as e:
        st.error(f"⚠️ Dashboard Display Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The Socratic AI is available for the Experimental Group only.")
        return
        
    if 'current_topic' not in st.session_state:
        st.info("👋 **Hello!** Please complete the Diagnostic Question in 'Learning Modules' first to start a conversation with the AI Tutor.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    st.caption("I help you think through the problem rather than giving you the answer.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Tell me more about your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Build context for the AI
        context = f"""
        You are a Socratic Tutor for Grade 10 Chemistry.
        Current Topic: {st.session_state.current_topic}
        Teacher's Instructional Goal: {st.session_state.logic_tree}
        Rules: Do not provide direct answers. Ask guiding questions to fix misconceptions.
        Student says: {prompt}
        """
        
        response = model.generate_content(context)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

def render_progress(uid):
    st.header("📈 My Progress Tracker")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = logs_df[logs_df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Progression", markers=True))
        else:
            st.info("No data yet. Complete your first module to see your growth chart!")
    except:
        st.error("Analytics engine currently unavailable.")
