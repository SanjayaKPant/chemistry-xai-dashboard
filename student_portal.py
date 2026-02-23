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
    # --- 1. Top-Level Main Title ---
    st.markdown("<h1 style='text-align: center; color: #0E1117;'>Advanced Chemistry Instructional Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #4B5563;'>Learning & Assessment Path</h2>", unsafe_allow_html=True)
    st.divider()

    # --- WORKFLOW: Logic to hide quiz if submitted ---
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
            
            # --- 2. Enhanced Module Header ---
            # Larger font for the Sub-topic
            st.markdown(f"""
                <div style="background-color:#E1E8F0; padding:10px; border-radius:5px; margin-bottom:10px;">
                    <h2 style="color:#1E3A8A; margin:0; font-size:26px;">📖 Module {q_num}: {row['Sub_Title']}</h2>
                </div>
            """, unsafe_allow_html=True)

            with st.container():
                # Side-by-Side Resources
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button("📄 View PDF Notes", row['File_Links (PDF/Images)'], use_container_width=True)
                with c2:
                    st.link_button("📺 Watch Video", row['Video_Links'], use_container_width=True)

                # --- 3. Compact Question Block ---
                # Reduced padding and margin to save space
                st.markdown(f"""
                    <div style="background-color:#F8FAFC; padding:12px; border-radius:8px; border-left: 4px solid #3B82F6; margin-top:15px; margin-bottom:10px;">
                        <span style="color:#64748B; font-weight:bold; font-size:14px; text-transform:uppercase;">Diagnostic Question {q_num}</span>
                        <p style="font-size:17px; font-weight:500; color:#1E293B; margin-top:5px;">{row['Diagnostic_Question']}</p>
                    </div>
                """, unsafe_allow_html=True)

                # 4-Tier Assessment UI
                ans = st.radio("Select Option:", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"q{idx}_t1")
                
                col_conf1, col_conf2 = st.columns(2)
                with col_conf1:
                    conf1 = st.select_slider("Answer Confidence:", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t2")
                
                reason = st.text_area("Scientific Reasoning:", placeholder="Explain the chemical principles behind your choice...", key=f"q{idx}_t3")
                
                with col_conf2:
                    conf2 = st.select_slider("Reasoning Confidence:", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t4")

                if st.button(f"Submit Assessment {q_num}", use_container_width=True):
                    success = log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], ans, conf1, reason, conf2, "Complete", "")
                    if success:
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        log_temporal_trace(st.session_state.user['User_ID'], "QUIZ_COMPLETE", row['Sub_Title'])
                        st.rerun()
            st.divider()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_progress(uid):
    st.markdown("<h1 style='color: #1E3A8A;'>📈 My Academic Progress</h1>", unsafe_allow_html=True)
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        u_logs = logs[logs['User_ID'].astype(str) == str(uid)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Questions Solved", len(u_logs))
        
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        u_turns = len(traces[(traces['User_ID'].astype(str) == str(uid)) & (traces['Event'] == 'AI_TURN')])
        m2.metric("Socratic Engagement", f"{u_turns} Turns")
        m3.metric("Status", "In Progress")

        if not u_logs.empty:
            st.subheader("Metacognitive Growth")
            cmap = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}
            u_logs['Initial'] = u_logs['Tier_2 (Confidence_Ans)'].map(cmap)
            u_logs['Reasoning'] = u_logs['Tier_4 (Confidence_Reas)'].map(cmap)
            
            fig = px.area(u_logs, x='Timestamps', y=['Initial', 'Reasoning'], 
                          title="Confidence Delta (Pre vs Post Reasoning)",
                          template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")

def render_ai_chat(group):
    if group not in ["School A", "Exp_A"]:
        st.warning("Access Restricted: Socratic Tutor is for experimental groups.")
        return
    if 'current_topic' not in st.session_state:
        st.info("Complete a module to activate the AI Tutor.")
        return

    st.markdown(f"<h1 style='color: #1E3A8A;'>🤖 Socratic Tutor</h1>", unsafe_allow_html=True)
    st.caption(f"Discussing: {st.session_state.current_topic}")

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except:
        st.error("AI HANDSHAKE FAILED.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        sys_p = (f"You are a Socratic Tutor for {st.session_state.current_topic}. "
                 f"Tree: {st.session_state.logic_tree}. Goal: Scaffolding. "
                 "Never reveal answers. Ask a conceptual follow-up.")
        
        try:
            resp = model.generate_content(f"{sys_p}\nStudent: {prompt}", request_options=RequestOptions(api_version='v1'))
            with st.chat_message("assistant"):
                st.markdown(resp.text)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
            log_temporal_trace(st.session_state.user['User_ID'], "AI_TURN", st.session_state.current_topic)
        except Exception as e:
            st.error(f"AI sync error: {e}")
