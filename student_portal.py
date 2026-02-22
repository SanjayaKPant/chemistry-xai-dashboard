import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    # Clean the student's group name
    student_group = str(user.get('Group', '')).strip().upper()
    
    st.markdown("""
        <style>
        .metric-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; text-align: center; }
        .instruction-container { background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; margin-bottom: 20px; }
        .sub-title-text { color: #007bff; font-weight: bold; font-size: 1.3rem; margin-bottom: 5px;}
        .question-box { background: #fffdf0; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin-top: 10px; color: #333; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Logged in as: {student_group}")
    
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
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><h3>Group</h3><p>{group}</p></div>', unsafe_allow_html=True)
    with m2: st.markdown('<div class="metric-card"><h3>Status</h3><p>Active</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Chapter</h3><p>Chemistry 10</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Year</h3><p>2026</p></div>', unsafe_allow_html=True)
    st.info("💡 **Instructions:** Go to 'Learning Modules' to find your assignments.")

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        raw_data = sh.worksheet("Instructional_Materials").get_all_values()
        
        if len(raw_data) < 2:
            st.warning("The teacher's database is currently empty.")
            return

        # --- DATA NORMALIZATION ---
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        # Force all column keys to lowercase/underscore
        df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]
        
        # Clean the Group column in the dataframe
        df['group_clean'] = df['group'].str.strip().str.upper()
        
        # FILTER: Match student group to the sheet's group
        my_lessons = df[df['group_clean'] == student_group]

        # DEBUG MODE: If it's empty, show why
        if my_lessons.empty:
            st.error(f"No modules matched for group: '{student_group}'")
            st.write("Available groups in the sheet:", df['group_clean'].unique())
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.markdown(f"## {row.get('main_title', 'Chapter')}")
                st.markdown(f"<div class='sub-title-text'>Topic: {row.get('sub_title', 'Concept')}</div>", unsafe_allow_html=True)
                
                # --- RESOURCES SECTION ---
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📖 Instructional Materials")
                c_pdf, c_vid = st.columns(2)
                
                f_url = str(row.get('file_link', '')).strip()
                if f_url and f_url.startswith("http"):
                    c_pdf.link_button("📥 View Study Materials", f_url, use_container_width=True)
                else:
                    c_pdf.caption("No PDFs provided.")
                    
                v_url = str(row.get('video_link', '')).strip()
                if v_url and v_url.startswith("http"):
                    c_vid.video(v_url)
                else:
                    c_vid.info("No video lecture.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- 4-TIER QUESTION ---
                st.markdown("---")
                st.subheader("🧪 4-Tier Concept Check")
                
                
                q_txt = row.get('q_text', 'Question body missing.')
                st.markdown(f"<div class='question-box'>{q_txt}</div>", unsafe_allow_html=True)
                
                with st.form(key=f"eval_{idx}"):
                    c1, c2 = st.columns(2)
                    opts = [row.get('oa'), row.get('ob'), row.get('oc'), row.get('od')]
                    opts = [o for o in opts if o and str(o).strip()]
                    
                    t1 = c1.radio("Tier 1: Answer", opts if opts else ["Options error"])
                    t2 = c2.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    r2c1, r2c2 = st.columns([2, 1])
                    t3 = r2c1.text_area("Tier 3: Reasoning")
                    t4 = r2c2.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit"):
                        t_id = row.get('sub_title', 'Unknown')
                        log_assessment(st.session_state.user['User_ID'], student_group, t_id, t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = t_id
                        st.session_state.logic_tree = row.get('socratic_tree', '')
                        st.success("✅ Assessment Saved! AI Tutor is now unlocked.")

    except Exception as e:
        st.error(f"System Error: {e}")

def render_ai_chat(school):
    if school != "School A":
        st.warning("The AI Tutor is currently enabled for Group A only.")
        return
    if 'current_topic' not in st.session_state:
        st.info("👋 Complete a module diagnostic first to unlock the AI.")
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
