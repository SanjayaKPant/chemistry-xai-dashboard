import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# Helper to get Nepal Time
def get_local_time():
    # Nepal is UTC + 5:45
    nepal_time = datetime.utcnow() + timedelta(hours=5, minutes=45)
    return nepal_time.strftime("%Y-%m-%d %H:%M:%S")

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
    st.title("🚀 Student Command Center")
    st.markdown(f"### Welcome, {user.get('Name')}!")
    st.info(f"Current Time (Nepal): {get_local_time()}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🎯 **Step 1:** Complete your Module Quiz.")
    with col2:
        st.warning("🤖 **Step 2:** Discuss your logic with the AI Tutor.")

def render_modules(student_group):
    # --- VISUAL HIERARCHY TITLES ---
    st.markdown("<h1 style='text-align: center; color: #0E1117;'>Advanced Chemistry Instructional Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4B5563;'>Metacognitive Learning Path</h3>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.get('last_submission_success'):
        st.success("✅ Assessment Submitted Successfully!")
        if st.button("🚀 Enter Socratic Chat", use_container_width=True):
            st.session_state.current_nav = "🤖 Socratic Tutor"
            st.session_state.last_submission_success = False
            st.rerun()
        return 

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            q_num = idx + 1
            
            # --- SUB-TOPIC (Enhanced Size) ---
            st.markdown(f"""
                <div style="background-color:#E1E8F0; padding:10px; border-radius:5px; margin-bottom:15px;">
                    <h2 style="color:#1E3A8A; margin:0; font-size:26px;">📖 Module {q_num}: {row['Sub_Title']}</h2>
                </div>
            """, unsafe_allow_html=True)

            # Resources
            c1, c2 = st.columns(2)
            with c1: st.link_button("📄 View PDF Notes", row['File_Links (PDF/Images)'], use_container_width=True)
            with c2: st.link_button("Watch Video", row['Video_Links'], use_container_width=True)

            # --- QUESTION BLOCK (Reduced Size) ---
            st.markdown(f"""
                <div style="background-color:#F8FAFC; padding:10px; border-radius:8px; border-left: 4px solid #3B82F6; margin-top:15px;">
                    <p style="font-size:16px; font-weight:500; color:#1E293B; margin:0;">{row['Diagnostic_Question']}</p>
                </div>
            """, unsafe_allow_html=True)

            # --- 4 TIERS (STRICT VERTICAL ORDER) ---
            st.write("")
            ans = st.radio(f"**Tier 1: Select your answer**", 
                           [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"q{idx}_t1")
            
            conf1 = st.select_slider(f"**Tier 2: How confident are you in this answer?**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t2")
            
            reason = st.text_area(f"**Tier 3: Scientific Reasoning**", 
                                  placeholder="Explain the chemical principles behind your choice...", key=f"q{idx}_t3")
            
            conf2 = st.select_slider(f"**Tier 4: How confident are you in your reasoning?**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t4")

            if st.button(f"Submit Assessment {q_num}", use_container_width=True):
                # BLOCK SUBMISSION IF REASON IS EMPTY
                if not reason.strip():
                    st.error("⚠️ Submission Rejected: You must provide your scientific reasoning in Tier 3.")
                elif len(reason.strip()) < 10:
                    st.warning("⚠️ Please provide a more detailed explanation (at least 10 characters).")
                else:
                    success = log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], ans, conf1, reason, conf2, "Complete", get_local_time())
                    if success:
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        log_temporal_trace(st.session_state.user['User_ID'], "QUIZ_SUBMIT", row['Sub_Title'])
                        st.rerun()
            st.divider()

    except Exception as e:
        st.error(f"Error: {e}")

def render_ai_chat(group):
    if group not in ["School A", "Exp_A"]:
        st.warning("The Socratic Tutor is currently enabled for experimental groups only.")
        return
    if 'current_topic' not in st.session_state:
        st.info("Please complete a Learning Module quiz to start the AI discussion.")
        return

    st.markdown(f"<h2 style='color: #1E3A8A;'>🤖 Socratic Assistant</h2>", unsafe_allow_html=True)
    st.caption(f"Active Session: {st.session_state.current_topic}")

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        st.error("AI Configuration failed.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        system_prompt = (f"You are a Socratic chemistry tutor. Topic: {st.session_state.current_topic}. "
                         f"Logic Tree instructions: {st.session_state.logic_tree}. "
                         "Goal: Use scaffolding. Never give the direct answer. Ask one conceptual question.")
        
        try:
            # FIXED: Removed api_version argument
            response = model.generate_content(f"{system_prompt}\nStudent: {prompt}")
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            log_temporal_trace(st.session_state.user['User_ID'], "AI_RESPONSE", st.session_state.current_topic)
        except Exception as e:
            st.error(f"AI sync error: {e}")

def render_progress(uid):
    st.title("📈 My Learning Progress")
    st.write("Tracking your mastery and confidence over time.")
    # Add your plotly chart logic here as needed
