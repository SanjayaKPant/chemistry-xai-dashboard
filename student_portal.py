import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from google.generativeai.types import RequestOptions

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Cohort: {student_group}")
    
    # Initialize navigation in session state
    if 'current_nav' not in st.session_state:
        st.session_state.current_nav = "🏠 Dashboard"
        
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_nav))
    st.session_state.current_nav = choice

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
    st.markdown(f"### Welcome, {user.get('Name')}!")
    st.info(f"Current Research Track: **{group}**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🎯 **Goal:** Complete the Diagnostic Quiz in 'Learning Modules'.")
    with col2:
        st.warning("🤖 **Mastery:** After the quiz, discuss your logic with the AI Tutor.")

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    
    # --- WORKFLOW: Hide quiz if submitted ---
    if st.session_state.get('last_submission_success'):
        st.success("✅ Thank You! Your answer has been submitted.")
        st.markdown("### Next Step: Socratic Discussion")
        st.write("To finish this module, you must now interact with the AI Tutor to validate your reasoning.")
        
        if st.button("🚀 Proceed to AI Tutor", use_container_width=True):
            st.session_state.current_nav = "🤖 Socratic Tutor"
            st.session_state.last_submission_success = False
            st.rerun()
        return 

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        if modules.empty:
            st.info("No modules available for your group yet.")
            return

        for idx, row in modules.iterrows():
            q_num = idx + 1
            with st.expander(f"📖 Module {q_num}: {row['Sub_Title']}", expanded=True):
                # 1. Resource Layout (Side-by-Side)
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button("📄 View PDF Notes", row['File_Links (PDF/Images)'], use_container_width=True)
                with c2:
                    st.link_button("📺 Watch Video", row['Video_Links'], use_container_width=True)

                st.divider()

                # 2. Styled Question (Blue & Large)
                st.markdown(f"""
                    <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; border-left: 5px solid #1E3A8A;">
                        <h3 style="color:#1E3A8A; margin:0;">Question {q_num}</h3>
                        <p style="font-size:18px; font-weight:bold; color:#333;">{row['Diagnostic_Question']}</p>
                    </div>
                """, unsafe_allow_html=True) # FIXED PARAMETER NAME HERE

                # 3. 4-Tier Assessment
                ans = st.radio("Choose the correct option:", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"q{idx}_t1")
                conf1 = st.select_slider("How sure are you about this answer?", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t2")
                reason = st.text_area("Why is this the correct answer scientifically?", key=f"q{idx}_t3")
                conf2 = st.select_slider("Confidence in your explanation?", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t4")

                if st.button(f"Submit Question {q_num}", use_container_width=True):
                    success = log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], ans, conf1, reason, conf2, "Complete", "")
                    if success:
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        log_temporal_trace(st.session_state.user['User_ID'], "QUIZ_COMPLETE", row['Sub_Title'])
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_progress(uid):
    st.title("📈 Professional Progress Analytics")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Summary Metrics
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        u_logs = logs[logs['User_ID'].astype(str) == str(uid)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Questions Solved", len(u_logs))
        
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        u_turns = len(traces[(traces['User_ID'].astype(str) == str(uid)) & (traces['Event'] == 'AI_TURN')])
        m2.metric("AI Tutor Turns", u_turns)
        
        m3.metric("Current Rank", "Chemistry Explorer")

        if not u_logs.empty:
            st.subheader("Confidence Evolution")
            # Map for charting
            cmap = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}
            u_logs['Initial'] = u_logs['Tier_2 (Confidence_Ans)'].map(cmap)
            u_logs['Reasoning'] = u_logs['Tier_4 (Confidence_Reas)'].map(cmap)
            
            fig = px.line(u_logs, x='Timestamps', y=['Initial', 'Reasoning'], 
                          title="Metacognitive Confidence (Pre vs Post Reasoning)",
                          markers=True, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Progress data unavailable: {e}")

def render_ai_chat(group):
    if group not in ["School A", "Exp_A"]:
        st.warning("The Socratic Tutor is active for the Experimental Group.")
        return
    if 'current_topic' not in st.session_state:
        st.info("Please submit a module diagnostic first to start the chat.")
        return

    st.title("🤖 Socratic AI Tutor")
    st.caption(f"Active Topic: {st.session_state.current_topic}")

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except:
        st.error("AI Configuration Error.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        sys_p = f"You are a Socratic Tutor. Topic: {st.session_state.current_topic}. Tree: {st.session_state.logic_tree}. Never give answers. Ask one guiding question. Max 2 sentences."
        
        try:
            resp = model.generate_content(f"{sys_p}\nStudent: {prompt}", request_options=RequestOptions(api_version='v1'))
            with st.chat_message("assistant"):
                st.markdown(resp.text)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
            log_temporal_trace(st.session_state.user['User_ID'], "AI_TURN", st.session_state.current_topic)
        except Exception as e:
            st.error(f"Connection error: {e}")
