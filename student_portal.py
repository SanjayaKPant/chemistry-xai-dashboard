import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    school = str(user.get('Group', 'School B')).strip()
    
    # CSS for Professional UI and Visibility
    st.markdown("""
        <style>
        .metric-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; text-align: center; }
        .instruction-container { background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; margin-bottom: 20px; }
        .sub-title-text { color: #007bff; font-weight: bold; font-size: 1.3rem; margin-bottom: 5px;}
        .question-box { background: #fffdf0; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin-top: 10px; font-weight: 500; color: #333; }
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
    with m2: st.markdown('<div class="metric-card"><h3>Status</h3><p>Active</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Course</h3><p>Chemistry</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Year</h3><p>2026</p></div>', unsafe_allow_html=True)
    st.info("💡 **Welcome!** Go to 'Learning Modules' to start your sub-shell configuration lesson.")

def render_modules(school):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        raw_data = sh.worksheet("Instructional_Materials").get_all_values()
        
        # --- ROBUST MAPPING ENGINE ---
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        # Force all columns to lowercase and remove spaces/parentheses
        df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]
        
        # Filter for the student's group (School A or School B)
        my_lessons = df[df['group'].str.upper() == school.upper()]

        if my_lessons.empty:
            st.warning(f"No modules found for {school}. Please ask your teacher to deploy a module for this group.")
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                # Module Headers
                st.markdown(f"## {row.get('main_title', 'Chemistry Module')}")
                st.markdown(f"<div class='sub-title-text'>Topic: {row.get('sub_title', 'Untitled Concept')}</div>", unsafe_allow_html=True)
                st.write(f"**Objectives:** {row.get('objectives', 'N/A')}")

                # --- FIX 1: VISIBLE MATERIALS ---
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📖 Instructional Materials")
                col_file, col_vid = st.columns([1, 1.2])
                
                with col_file:
                    st.write("**📄 Study PDF/Images**")
                    f_link = str(row.get('file_link', '')).strip()
                    if f_link and f_link.startswith("http"):
                        st.link_button("📥 Download/View Resources", f_link, use_container_width=True)
                    else:
                        st.caption("No files uploaded.")

                with col_vid:
                    st.write("**🎥 Video Lecture**")
                    v_link = str(row.get('video_link', '')).strip()
                    if v_link and v_link.startswith("http"):
                        st.video(v_link)
                    else:
                        st.info("No video provided.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- FIX 2: VISIBLE 4-TIER QUESTION ---
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic Check")
                
                
                q_text = row.get('q_text', 'No question content found.')
                st.markdown(f"<div class='question-box'>{q_text}</div>", unsafe_allow_html=True)
                
                with st.form(key=f"eval_{idx}"):
                    c1, c2 = st.columns(2)
                    opts = [row.get('oa'), row.get('ob'), row.get('oc'), row.get('od')]
                    opts = [o for o in opts if o and str(o).strip()]
                    
                    t1 = c1.radio("Tier 1: Select Answer", opts if opts else ["No options provided"])
                    t2 = c2.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    r2c1, r2c2 = st.columns([2, 1])
                    t3 = r2c1.text_area("Tier 3: Reasoning (Explain why)")
                    t4 = r2c2.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock AI Tutor"):
                        t_id = row.get('sub_title', 'General')
                        log_assessment(st.session_state.user['User_ID'], school, t_id, t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = t_id
                        st.session_state.logic_tree = row.get('socratic_tree', '')
                        st.success("✅ Success! You can now talk to the Socratic Tutor.")

    except Exception as e:
        st.error(f"⚠️ Portal Error: {e}")

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
