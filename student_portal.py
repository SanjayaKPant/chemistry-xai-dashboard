import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    # Professional Styling
    st.markdown("""
        <style>
        .main-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 20px; }
        .instruction-box { background: #f8f9fa; border-left: 5px solid #007bff; padding: 15px; border-radius: 5px; }
        .metric-text { font-size: 24px; font-weight: bold; color: #007bff; }
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
    st.title("🚀 Student Learning Dashboard")
    
    # ROW 1: Filling unused space with professional metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Current Group", school)
    with c2: st.metric("Modules Started", "4")
    with c3: st.metric("Accuracy", "78%")
    with c4: st.metric("Streak", "3 Days")

    st.markdown("---")
    
    # ROW 2: Professional Content Area
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("📢 Recent Activity")
        st.info("💡 **Tip:** Complete the diagnostic questions in 'Learning Modules' to unlock personalized AI tutoring.")
        # Placeholder for real assignment feed
        st.write("### 📝 Upcoming Tasks")
        st.write("• Chemical Bonding Quiz - Due Friday")
        st.write("• Periodic Table Assignment - Due Monday")
    
    with col_right:
        st.subheader("📊 Quick Progress")
                st.progress(0.4)
        st.caption("Overall Course Completion: 40%")

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
                # HEADER: Title & Subtitle (Restored)
                st.markdown(f"## {row.get('MAIN_TITLE', 'Chapter')} : {row.get('SUB_TITLE', 'Concept')}")
                st.markdown(f"**🎯 Objectives:** {row.get('LEARNING_OBJECTIVES', 'Review key concepts.')}")
                
                # SECTION 1: DEDICATED INSTRUCTIONAL MATERIALS (Restored & Optimized)
                st.markdown("#### 📖 Instructional Materials")
                m1, m2 = st.columns([1, 1.2])
                with m1:
                    st.markdown('<div class="instruction-box">', unsafe_allow_html=True)
                    st.write("**Reference Files:**")
                    links = str(row.get('FILE_LINK', '')).split(", ")
                    for i, l in enumerate(links):
                        if l.strip(): st.link_button(f"📄 View Resource {i+1}", l.strip(), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                with m2:
                    if row.get('VIDEO_LINK'):
                        st.video(row.get('VIDEO_LINK'))
                    else:
                        st.info("No video tutorial available for this concept.")

                # SECTION 2: 4-TIER DIAGNOSTIC (Compressed Grid Layout)
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic Assessment")
                st.write(f"**Question:** {row.get('Q_TEXT', 'Please answer based on the materials above.')}")
                
                                
                with st.form(key=f"diag_{idx}"):
                    # ROW A: Tier 1 & 2
                    a1, a2 = st.columns(2)
                    t1 = a1.radio("Tier 1: Select Answer", [row.get('OA'), row.get('OB'), row.get('OC'), row.get('OD')])
                    t2 = a2.select_slider("Tier 2: Answer Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    # ROW B: Tier 3 & 4
                    b1, b2 = st.columns([2, 1])
                    t3 = b1.text_area("Tier 3: Scientific Reasoning (Explain why)")
                    t4 = b2.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Start AI Tutoring"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.logic_tree = row['SOCRATIC_TREE']
                        st.success("✅ Submitted! You can now use the Socratic Tutor for this topic.")
                        log_temporal_trace(st.session_state.user['User_ID'], "MODULE_COMPLETE", row['SUB_TITLE'])

    except Exception as e:
        st.error(f"Module Display Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The Socratic AI is currently enabled for Experimental Group A only.")
        return
    
    if 'current_topic' not in st.session_state:
        st.info("👋 **Welcome to the AI Lab.** Please complete a Diagnostic Question in the 'Learning Modules' tab first to start a session.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    st.caption("I'm here to help you refine your scientific reasoning, not just give you answers.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Tell me more about your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        context = f"Topic: {st.session_state.current_topic}. Teacher's Socratic Plan: {st.session_state.logic_tree}. Student says: {prompt}."
        
        response = model.generate_content(context)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

def render_progress(uid):
    st.header("📈 My Progress Tracker")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            fig = px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Over Time", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet. Complete your first module to see your growth chart!")
    except:
        st.error("Progress data currently unavailable.")
