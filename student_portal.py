import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.markdown("""
        <style>
        .instruction-container { background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 6px solid #007bff; margin-bottom: 20px; }
        .sub-title-text { color: #007bff; font-weight: bold; font-size: 1.3rem; margin-bottom: 5px;}
        .question-box { background: #fffdf0; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin-top: 10px; font-weight: 500; color: #333; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {student_group}")
    
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
    st.info(f"Welcome, Scientist. You are participating in the **{group}** study group.")
    
    st.success("Please navigate to 'Learning Modules' to begin your current chemistry assignment.")

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        df = pd.DataFrame(ws.get_all_records())

        # Filtering based on your specific CSV/Sheet structure
        my_lessons = df[df['Group'].str.strip() == student_group]

        if my_lessons.empty:
            st.warning(f"No modules currently assigned to {student_group}.")
            return

        for idx, row in my_lessons.iterrows():
            with st.container():
                st.markdown(f"## {row.get('Main_Title')}")
                st.markdown(f"<div class='sub-title-text'>Topic: {row.get('Sub_Title')}</div>", unsafe_allow_html=True)
                st.write(f"**Learning Objectives:** {row.get('Learning_Objectives')}")

                # 1. MATERIALS SECTION
                st.markdown('<div class="instruction-container">', unsafe_allow_html=True)
                st.write("#### 📖 Instructional Materials")
                col_file, col_vid = st.columns(2)
                
                f_link = str(row.get('File_Links (PDF/Images)', '')).strip()
                if f_link.startswith("http"):
                    col_file.link_button("📥 Open Study PDF", f_link, use_container_width=True)
                
                v_link = str(row.get('Video_Links', '')).strip()
                if v_link.startswith("http"):
                    col_vid.video(v_link)
                st.markdown('</div>', unsafe_allow_html=True)

                # 2. 4-TIER QUESTION SECTION
                st.divider()
                st.subheader("🧪 4-Tier Diagnostic Check")
                
                
                st.markdown(f"<div class='question-box'>{row.get('Diagnostic_Question')}</div>", unsafe_allow_html=True)
                
                with st.form(key=f"eval_{idx}"):
                    c1, c2 = st.columns(2)
                    opts = [row.get('Option_A'), row.get('Option_B'), row.get('Option_C'), row.get('Option_D')]
                    opts = [str(o) for o in opts if o and str(o).strip()]
                    
                    t1 = c1.radio("Tier 1: Answer Choice", opts if opts else ["Options Missing"])
                    t2 = c2.select_slider("Tier 2: Answer Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    t3 = st.text_area("Tier 3: Reasoning (Explain why you chose that answer)")
                    t4 = st.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock AI Tutor"):
                        # Logging to Assessment_Logs
                        log_assessment(st.session_state.user['User_ID'], student_group, row.get('Sub_Title'), t1, t2, t3, t4, "Complete", "")
                        
                        # Store session context for AI
                        st.session_state.current_topic = row.get('Sub_Title')
                        st.session_state.logic_tree = row.get('Socratic_Tree')
                        
                        st.success("✅ Success! Your response is logged. You can now talk to the AI Tutor.")
                        log_temporal_trace(st.session_state.user['User_ID'], "SUBMIT_DIAGNOSTIC", row.get('Sub_Title'))

    except Exception as e:
        st.error(f"⚠️ System Error: {e}")

def render_ai_chat(school):
    # Research logic: AI active for experimental groups only
    if school not in ["School A", "Exp_A"]:
        st.warning("The Socratic AI Tutor is currently disabled for your group.")
        return
        
    if 'current_topic' not in st.session_state:
        st.info("👋 Please complete a Diagnostic Check in 'Learning Modules' first to unlock the AI.")
        return

    st.header(f"🤖 Socratic Tutor: {st.session_state.current_topic}")
    
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            # FIX: Using GEMINI_API_KEY to match your specific Streamlit secrets
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # High-level Socratic Pedagogy Prompt
            system_prompt = f"""
            YOU ARE: A world-class Socratic Chemistry Tutor for Grade 10 students.
            CONTEXT: The topic is '{st.session_state.current_topic}' from 'Classification of Elements'.
            TEACHER'S LOGIC TREE: {st.session_state.logic_tree}
            
            SCIENTIFIC PEDAGOGY RULES:
            1. NEVER give the student the answer.
            2. If they are wrong, ask a question about periodic trends, nuclear charge, or valence shells.
            3. Use textbook terms: Aufbau principle, n+l rule, electronic configuration.
            4. Keep responses brief (under 3 sentences).
            """
            
            response = model.generate_content(f"{system_prompt}\nStudent: {prompt}")
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            log_temporal_trace(st.session_state.user['User_ID'], "AI_CONVERSATION", st.session_state.current_topic)
            
        except Exception as e:
            st.error(f"AI Connection Error: {e}. Check if GEMINI_API_KEY is correctly set in Secrets.")

def render_progress(uid):
    st.header("📈 My Learning Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        
        if not user_df.empty:
            # Plotly Chart for confidence tracking
            fig = px.line(user_df, x="Timestamps", y="Tier_2 (Confidence_Ans)", 
                          title="Confidence Over Time", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No assessment data found yet. Complete a module to see your progress.")
    except Exception as e:
        st.error(f"Analytics Error: {e}")
