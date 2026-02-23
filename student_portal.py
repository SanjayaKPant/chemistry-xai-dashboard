import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- HELPERS ---
def get_nepal_time():
    # Adjusts UTC to Nepal Time (UTC +5:45)
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    # Reset AI chat if switching groups/users
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
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
    st.info(f"Local Time (Nepal): {get_nepal_time()}")
    
    c1, c2 = st.columns(2)
    with c1: st.success("🎯 Complete the Diagnostic Quiz first.")
    with c2: st.warning("🤖 Then, discuss logic with the AI.")

def render_modules(student_group):
    st.markdown("<h1 style='text-align: center;'>Advanced Chemistry Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Assessment & Scaffolding</h3>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.get('last_submission_success'):
        st.success("✅ Assessment Recorded in Nepal Time!")
        if st.button("🚀 Start Socratic Discussion", use_container_width=True):
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
            # Module Header (Increased Size)
            st.markdown(f"<h2 style='color:#1E3A8A;'>📖 Module: {row['Sub_Title']}</h2>", unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a: st.link_button("📄 PDF Notes", row['File_Links (PDF/Images)'], use_container_width=True)
            with col_b: st.link_button("📺 Video", row['Video_Links'], use_container_width=True)

            # Compact Question Box
            st.markdown(f"""<div style="background:#F0F2F6; padding:15px; border-radius:10px; border-left:5px solid #1E3A8A; margin:10px 0;">
                <p style="font-size:18px; margin:0;"><b>Question:</b> {row['Diagnostic_Question']}</p>
            </div>""", unsafe_allow_html=True)

            # --- STRICT VERTICAL 4-TIERS ---
            t1 = st.radio("Tier 1: Select Answer", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"q{idx}_t1")
            t2 = st.select_slider("Tier 2: Answer Confidence", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t2")
            t3 = st.text_area("Tier 3: Scientific Reasoning (Mandatory)", placeholder="Explain why...", key=f"q{idx}_t3")
            t4 = st.select_slider("Tier 4: Reasoning Confidence", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t4")

            if st.button(f"Submit Module Assessment", use_container_width=True):
                if len(t3.strip()) < 15: # REASONING VALIDATION
                    st.error("❌ Your reasoning is too short. Please provide a scientific explanation before submitting.")
                else:
                    # Log with current Nepal Time
                    ts = get_nepal_time()
                    success = log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], t1, t2, t3, t4, "Complete", ts)
                    if success:
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        st.rerun()
            st.divider()
    except Exception as e:
        st.error(f"Module Error: {e}")

def render_ai_chat(group):
    if group not in ["School A", "Exp_A"]:
        st.warning("AI Tutor is reserved for Experimental Groups.")
        return
    if 'current_topic' not in st.session_state:
        st.info("Please submit your quiz answers first.")
        return

    st.title("🤖 Socratic AI Tutor")
    
    # Configure AI safely
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        st.error("AI Configuration Error.")
        return

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning further..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        sys_instr = f"You are a Socratic chemistry tutor. Topic: {st.session_state.current_topic}. Logic Tree: {st.session_state.logic_tree}. Never give answers. Ask one guiding question to help student find the truth."
        
        try:
            # FIXED: Removed the 'api_version' argument causing the error
            response = model.generate_content(f"{sys_instr}\nStudent says: {prompt}")
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"AI sync error: {e}")

def render_progress(uid):
    st.title("📈 My Progress")
    st.write("Your learning history and confidence levels are tracked here.")
    # Placeholder for graph logic
    st.info("Data visualization will refresh on your next login.")
