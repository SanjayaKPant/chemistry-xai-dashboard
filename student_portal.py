import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
# Use this to call functions from database_manager.py
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    # Ensure group matches the sheet (e.g., "School A") 
    student_group = str(user.get('Group', 'School A')).strip()
    
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
    st.sidebar.info(f"Assigned Group: {student_group}")
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
    with m2: st.markdown('<div class="metric-card"><h3>Course</h3><p>Chemistry 10</p></div>', unsafe_allow_html=True)
    with m3: st.markdown('<div class="metric-card"><h3>Status</h3><p>Active</p></div>', unsafe_allow_html=True)
    with m4: st.markdown('<div class="metric-card"><h3>Task</h3><p>Diagnostic</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📢 Teacher's Guidance")
    st.info("💡 **Welcome!** Please complete the Diagnostic Question in 'Learning Modules' to unlock the AI Tutor.")

def render_modules(student_group):
    st.header("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        # get_all_records() automatically uses the first row as keys 
        data = sh.worksheet("Instructional_Materials").get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            st.warning("No modules have been deployed yet.")
            return

        # Filtering logic: Must match "Group" column in CSV 
        my_lessons = df[df['Group'].str.strip() == student_group]

        if my_lessons.empty:
            st.error(f"No modules assigned to {student_group}.")
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.markdown(f"## {row.get('Main_Title')}")
                st.markdown(f"<div class='sub-title-text'>{row.get('Sub_Title')}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='objective-text'>🎯 {row.get('Learning_Objectives')}</span>", unsafe_allow_html=True)

                # --- PART 1: INSTRUCTIONAL MATERIALS ---
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📦 Lesson Resources")
                col_file, col_vid = st.columns([1, 1.2])
                
                with col_file:
                    st.write("**📄 Reference Materials**")
                    # Matching column: 'File_Links (PDF/Images)' 
                    f_link = str(row.get('File_Links (PDF/Images)', '')).strip()
                    if f_link.startswith("http"):
                        st.link_button("Open Resource", f_link, use_container_width=True)
                    else:
                        st.caption("No PDFs uploaded.")

                with col_vid:
                    st.write("**🎥 Video Lesson**")
                    # Matching column: 'Video_Links' 
                    vid_url = str(row.get('Video_Links', '')).strip()
                    if vid_url.startswith("http"):
                        st.video(vid_url)
                    else:
                        st.info("No video lecture provided.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- PART 2: 4-TIER DIAGNOSTIC ---
                st.markdown("---")
                st.subheader("🧪 4-Tier Diagnostic Check")
                
                # Matching column: 'Diagnostic_Question' 
                q_body = row.get('Diagnostic_Question', 'No question text provided.')
                st.markdown(f"<div class='question-box'>Q: {q_body}</div>", unsafe_allow_html=True)
                
                with st.form(key=f"eval_{idx}"):
                    r1_c1, r1_c2 = st.columns(2)
                    # Matching columns: Option_A, Option_B, Option_C, Option_D 
                    opts = [row.get('Option_A'), row.get('Option_B'), row.get('Option_C'), row.get('Option_D')]
                    opts = [str(o) for o in opts if o]
                    
                    t1 = r1_c1.radio("Tier 1: Answer Choice", opts)
                    t2 = r1_c2.select_slider("Tier 2: Confidence level", ["Unsure", "Sure", "Very Sure"])
                    
                    r2_c1, r2_c2 = st.columns([2, 1])
                    t3 = r2_c1.text_area("Tier 3: Reasoning (Briefly explain your choice)")
                    t4 = r2_c2.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock Tutor"):
                        # Log using database_manager functions
                        log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], t1, t2, t3, t4, "Submitted", "")
                        
                        # Set Socratic Context
                        st.session_state.current_topic = row['Sub_Title']
                        # Matching column: 'Socratic_Tree' 
                        st.session_state.logic_tree = row['Socratic_Tree']
                        
                        st.success(f"✅ Success! AI Tutor unlocked for {row['Sub_Title']}.")
                        log_temporal_trace(st.session_state.user['User_ID'], "SUBMITTED_DIAGNOSTIC", row['Sub_Title'])

    except Exception as e:
        st.error(f"⚠️ Error loading modules: {e}")

def render_ai_chat(school):
    # Research constraint: Only Experimental Group gets the Socratic AI
    if school not in ["School A", "Exp_A"]:
        st.warning("The Socratic AI Tutor is currently active for the Experimental Group only.")
        return
        
    if 'current_topic' not in st.session_state:
        st.info("👋 **Welcome!** Please complete the diagnostic question in 'Learning Modules' to activate the Socratic Tutor.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Discuss your chemical reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # --- SOCRATIC ENGINE CONFIGURATION ---
        try:
            # Note: Using GEMINI_API_KEY to match your specific secrets
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            system_instruction = f"""
            ROLE: PhD Chemistry Socratic Educator.
            CONTEXT: Grade 10 - Classification of Elements.
            TOPIC: {st.session_state.current_topic}.
            PEDAGOGY: Use Socratic Scaffolding. Never provide direct answers. 
            If a student is confused about periodic trends, ask them about 'Effective Nuclear Charge' or 'Shell Number'.
            Refer to the Teacher's Logic Tree: {st.session_state.logic_tree}
            """
            
            response = model.generate_content(f"{system_instruction}\nStudent input: {prompt}")
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Log for research analytics
            log_temporal_trace(st.session_state.user['User_ID'], "SOCRATIC_INTERACTION", st.session_state.current_topic)
            
        except KeyError:
            st.error("Secret Key Mismatch: Ensure your secret is named 'GEMINI_API_KEY' in Streamlit settings.")
def render_progress(uid):
    st.header("📈 My Progress Tracker")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        # Match 'Assessment_Logs' worksheet
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            st.plotly_chart(px.line(user_df, x="Timestamp", y="Tier_2", title="Confidence Progression", markers=True))
        else:
            st.info("No data yet. Complete your first module to see your growth!")
    except:
        st.error("Analytics engine currently unavailable.")
