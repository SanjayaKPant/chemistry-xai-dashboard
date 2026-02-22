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
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Your Assigned Group: **{student_group}**")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        st.title("🚀 Student Dashboard")
        st.write(f"Welcome back, {user.get('Name')}!")
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_modules(student_group):
    st.title("📚 Learning Path")
    
    # --- VPS EMERGENCY DEBUG CONSOLE (STAYS AT TOP) ---
    st.warning("🔬 VPS System Diagnostic Console")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        raw_rows = ws.get_all_values()
        
        if len(raw_rows) < 2:
            st.error("The Google Sheet is empty! Please deploy a module from the Teacher Portal.")
            return

        # Create the DataFrame
        df = pd.DataFrame(raw_rows[1:], columns=raw_rows[0])
        
        # Show exactly what is in the sheet right now
        with st.expander("🛠️ STEP 1: CLICK HERE TO SEE ALL DATA IN SHEET", expanded=True):
            st.write("Below is every row the app sees in your Google Sheet:")
            st.dataframe(df) 
            st.write("End of data check.")

        # --- NORMALIZATION & FILTERING ---
        df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]
        
        # We search for the group. We use .upper() to avoid "School A" vs "school a" errors.
        df['group_match'] = df['group'].str.strip().str.upper()
        target_group = student_group.strip().upper()
        
        my_lessons = df[df['group_match'] == target_group]

        st.info(f"Filtering for Group: `{target_group}`")

        if my_lessons.empty:
            st.error(f"❌ No lessons matched for `{target_group}`.")
            st.write("Groups available in your sheet are:", df['group_match'].unique().tolist())
        else:
            st.success(f"✅ Found {len(my_lessons)} lesson(s) for you!")
            
            for idx, row in my_lessons.iterrows():
                with st.container():
                    st.divider()
                    st.header(f"📖 {row.get('main_title')}")
                    st.subheader(row.get('sub_title'))
                    
                    # Materials
                    c1, c2 = st.columns(2)
                    f_url = str(row.get('file_link', '')).strip()
                    if f_url.startswith("http"):
                        c1.link_button("📂 View Lesson PDF/Notes", f_url)
                    
                    v_url = str(row.get('video_link', '')).strip()
                    if v_url.startswith("http"):
                        c2.video(v_url)

                    # 4-Tier Form
                    st.write("---")
                    st.markdown(f"**Question:** {row.get('q_text')}")
                    with st.form(key=f"form_{idx}"):
                        opts = [row.get('oa'), row.get('ob'), row.get('oc'), row.get('od')]
                        opts = [o for o in opts if o]
                        ans = st.radio("Tier 1: Answer", opts)
                        conf = st.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"])
                        reason = st.text_area("Tier 3: Reasoning")
                        r_conf = st.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                        
                        if st.form_submit_button("Submit"):
                            log_assessment(st.session_state.user['User_ID'], student_group, row.get('sub_title'), ans, conf, reason, r_conf, "Logged", "")
                            st.session_state.current_topic = row.get('sub_title')
                            st.session_state.logic_tree = row.get('socratic_tree')
                            st.balloons()

    except Exception as e:
        st.error(f"Critical System Failure: {e}")

# ... (render_ai_chat and render_progress functions remain identical)

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
