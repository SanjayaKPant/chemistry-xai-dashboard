import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    # Standardize student group info
    student_group = str(user.get('Group', '')).strip()
    
    st.markdown("""
        <style>
        .instruction-container { background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; margin-bottom: 20px; }
        .sub-title-text { color: #007bff; font-weight: bold; font-size: 1.3rem; }
        .question-box { background: #fffdf0; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; color: #333; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.write(f"**Current Group:** `{student_group}`")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        st.title("🚀 Student Dashboard")
        st.info(f"Checking for modules assigned to: **{student_group}**")
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        data = ws.get_all_records()
        
        if not data:
            st.warning("The database worksheet is empty. Ask the teacher to deploy a module.")
            return

        df = pd.DataFrame(data)
        # 1. Clean column names (Teacher uses 'sub_title', student portal needs to match)
        df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]

        # --- DEBUG SECTION (ONLY VISIBLE TO HELP US FIND THE DATA) ---
        with st.expander("🔍 VPS Debug: View Raw Sheet Data"):
            st.write("Student Group in App:", f"`{student_group}`")
            st.write("All Groups found in Sheet:", df['group'].unique().tolist())
            st.dataframe(df[['main_title', 'sub_title', 'group']])

        # 2. Case-Insensitive Filtering
        my_lessons = df[df['group'].str.strip().str.upper() == student_group.strip().upper()]

        if my_lessons.empty:
            st.error(f"⚠️ No matches found for '{student_group}'.")
            st.info("Look at the Debug table above. Does the group name in the sheet match exactly?")
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.markdown(f"## {row.get('main_title', 'Chapter')}")
                st.markdown(f"<div class='sub-title-text'>{row.get('sub_title', 'Topic')}</div>", unsafe_allow_html=True)
                
                # Resources
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📖 Instructional Materials")
                col1, col2 = st.columns(2)
                
                f_link = str(row.get('file_link', '')).strip()
                if f_link.startswith("http"):
                    col1.link_button("📥 Download PDF/Materials", f_link, use_container_width=True)
                
                v_link = str(row.get('video_link', '')).strip()
                if v_link.startswith("http"):
                    col2.video(v_link)
                st.markdown('</div>', unsafe_allow_html=True)

                # 4-Tier Question
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic Check")
                
                st.markdown(f"<div class='question-box'>{row.get('q_text', 'Question missing')}</div>", unsafe_allow_html=True)
                
                with st.form(key=f"q_{idx}"):
                    # Dynamic options mapping
                    opts = [row.get('oa'), row.get('ob'), row.get('oc'), row.get('od')]
                    opts = [o for o in opts if o]
                    
                    c1, c2 = st.columns(2)
                    t1 = c1.radio("Tier 1: Select Answer", opts if opts else ["Options missing"])
                    t2 = c2.select_slider("Tier 2: Answer Confidence", ["Low", "Medium", "High"])
                    
                    r2c1, r2c2 = st.columns([2, 1])
                    t3 = r2c1.text_area("Tier 3: Reasoning")
                    t4 = r2c2.select_slider("Tier 4: Reasoning Confidence", ["Low", "Medium", "High"])
                    
                    if st.form_submit_button("Submit"):
                        log_assessment(st.session_state.user['User_ID'], student_group, row.get('sub_title'), t1, t2, t3, t4, "Complete", "")
                        st.session_state.current_topic = row.get('sub_title')
                        st.session_state.logic_tree = row.get('socratic_tree')
                        st.success("✅ Assessment Saved!")

    except Exception as e:
        st.error(f"Loading Error: {e}")

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
