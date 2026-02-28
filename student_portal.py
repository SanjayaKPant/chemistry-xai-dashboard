import streamlit as st
import pandas as pd
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- SOCRATIC ENGINE NORMS ---
SOCRATIC_NORMS = """
You are Saathi AI, a Socratic Chemistry Tutor.
1. NEVER give the student the answer.
2. The student has just answered a diagnostic question. Use their Tier 1 answer and Tier 3 reasoning to start the dialogue.
3. Your goal is to lead them to conceptual clarity through questions.
4. When they explain the concept correctly, you MUST include the exact string [MASTERY_DETECTED] in your response.
"""

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45))

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.stop()
        
    user = st.session_state.user
    uid, group = str(user.get('User_ID', '')).upper(), str(user.get('Group', 'Control'))

    # NAVIGATION LOGIC
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Saathi AI", "📈 My Progress"]
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "🏠 Dashboard"

    # Sidebar Navigation with Sync
    choice = st.sidebar.radio("Navigation", menu, 
                              index=menu.index(st.session_state.current_tab),
                              key="nav_radio_main")
    
    # Sync choice back to state
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard": render_dashboard(user)
    elif choice == "📚 Learning Modules": render_modules(uid, group)
    elif choice == "🤖 Saathi AI": render_ai_chat(uid, group)
    elif choice == "📈 My Progress": render_progress(uid)

def render_dashboard(user):
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.info("Goal: Complete the diagnostic questions in 'Learning Modules' to unlock Saathi AI.")

def render_modules(uid, group):
    st.header("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    
    finished = logs_df[(logs_df['User_ID'].astype(str).str.upper() == uid) & (logs_df['Status'] == 'POST')]['Module_ID'].tolist()
    available = m_df[m_df['Group'].astype(str) == group]
    
    active_row = None
    for _, row in available.iterrows():
        if row['Sub_Title'] not in finished:
            active_row = row
            break

    if active_row is not None:
        st.subheader(active_row['Sub_Title'])
        with st.form("tier_1_4_form"):
            st.write(f"**Question:** {active_row['Diagnostic_Question']}")
            opts = [active_row['Option_A'], active_row['Option_B'], active_row['Option_C'], active_row['Option_D']]
            t1 = st.radio("Select Answer:", opts)
            t2 = st.select_slider("How sure are you about this answer?", ["Guessing", "Unsure", "Sure", "Very Sure"])
            t3 = st.text_area("Explain your reasoning (Why did you choose this?):")
            t4 = st.select_slider("How sure are you about your explanation?", ["Guessing", "Unsure", "Sure", "Very Sure"])
            
            if st.form_submit_button("Submit & Start Discussion"):
                if len(t3.strip()) < 5:
                    st.error("Please provide a reasoning to continue.")
                else:
                    # 1. Log to Database
                    log_assessment(uid, group, active_row['Sub_Title'], t1, t2, t3, t4, "INITIAL", get_nepal_time().strftime("%Y-%m-%d %H:%M"))
                    
                    # 2. Lock Module into Session for AI
                    st.session_state.active_module = active_row.to_dict()
                    
                    # 3. Setup AI Context
                    st.session_state.messages = [
                        {"role": "system", "content": SOCRATIC_NORMS},
                        {"role": "assistant", "content": f"I see you chose '{t1}' because: '{t3}'. Let's explore that. How would this concept apply if we changed the conditions?"}
                    ]
                    
                    # 4. Trigger Automatic Redirect
                    st.session_state.current_tab = "🤖 Saathi AI"
                    st.rerun()
    else:
        st.success("All modules complete! Check 'My Progress'.")

def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if not module:
        st.warning("⚠️ Please complete a module question first to unlock the AI.")
        return

    # Split View: Question on Left, Chat on Right
    col_q, col_c = st.columns([1, 2])
    
    with col_q:
        st.markdown("### 📝 Question Context")
        st.info(f"**Module:** {module['Sub_Title']}")
        st.write(module['Diagnostic_Question'])
        st.write(f"- {module['Option_A']}\n- {module['Option_B']}\n- {module['Option_C']}\n- {module['Option_D']}")

    with col_c:
        if st.session_state.get('mastery_triggered'):
            render_tier_5_6(uid, group, module)
            return

        st.subheader("🤖 Chat with Saathi AI")
        for m in st.session_state.messages[1:]:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Reply to Saathi..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # API Call
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
            ai_reply = resp.choices[0].message.content
            
            # Mastery Check
            if "[MASTERY_DETECTED]" in ai_reply:
                st.session_state.mastery_triggered = True
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            log_temporal_trace(uid, "CHAT_MSG", f"Mod: {module['Sub_Title']} | {prompt}")
            st.rerun()

def render_tier_5_6(uid, group, module):
    st.success("🌟 Mastery Detected! Final Step / अन्तिम चरण")
    with st.form("t56_form"):
        t5 = st.radio("Final Answer:", [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']])
        t6 = st.select_slider("Final Confidence:", ["Guessing", "Unsure", "Sure", "Very Sure"])
        if st.form_submit_button("Complete Module"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", "Mastered", "N/A", "POST", 
                           get_nepal_time().strftime("%Y-%m-%d %H:%M"), t5, t6)
            # Reset for next module
            st.session_state.active_module = None
            st.session_state.mastery_triggered = False
            st.session_state.messages = []
            st.session_state.current_tab = "🏠 Dashboard"
            st.rerun()

def render_progress(uid):
    st.header("📈 My Progress")
    st.write("Metacognitive growth analysis arriving soon...")
