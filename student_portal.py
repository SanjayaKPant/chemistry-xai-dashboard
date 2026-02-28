import streamlit as st
import pandas as pd
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- RESEARCH CONSTANTS ---
SOCRATIC_NORMS = """
You are Saathi AI, a Socratic Chemistry Tutor. 
1. NEVER give the student the answer. 
2. Use the student's initial Tier 1 answer and Tier 3 reasoning to start the dialogue.
3. Ask one probing question at a time to uncover their mental model.
4. When they explain the concept correctly, you MUST output the exact string: [MASTERY_DETECTED]
"""

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45))

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.stop()
        
    user = st.session_state.user
    uid, group = str(user.get('User_ID', '')).upper(), str(user.get('Group', 'Control'))

    # 1. NAVIGATION ENGINE
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Saathi AI", "📈 My Progress"]
    
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "🏠 Dashboard"

    # Sidebar Sync
    choice = st.sidebar.radio("Navigation", menu, 
                              index=menu.index(st.session_state.current_tab),
                              key="nav_radio_engine")
    
    # Keep the state updated if the user manually clicks
    st.session_state.current_tab = choice

    # 2. ROUTING LOGIC
    if st.session_state.current_tab == "🏠 Dashboard":
        render_dashboard(user)
    elif st.session_state.current_tab == "📚 Learning Modules":
        render_modules(uid, group)
    elif st.session_state.current_tab == "🤖 Saathi AI":
        render_ai_chat(uid, group)
    elif st.session_state.current_tab == "📈 My Progress":
        render_progress(uid)

def render_dashboard(user):
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.info("Complete your diagnostic questions in 'Learning Modules' to start your Socratic session.")

def render_modules(uid, group):
    st.header("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    
    finished = logs_df[(logs_df['User_ID'].astype(str).str.upper() == uid) & (logs_df['Status'] == 'POST')]['Module_ID'].tolist()
    
    # Filter for active module
    available = m_df[m_df['Group'].astype(str) == group]
    active_row = None
    for _, row in available.iterrows():
        if row['Sub_Title'] not in finished:
            active_row = row
            break

    if active_row is not None:
        st.subheader(f"Module: {active_row['Sub_Title']}")
        with st.form("t14_research_form"):
            st.write(f"**Question:** {active_row['Diagnostic_Question']}")
            opts = [active_row['Option_A'], active_row['Option_B'], active_row['Option_C'], active_row['Option_D']]
            t1 = st.radio("Select Answer:", opts)
            t2 = st.select_slider("Confidence (Answer):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            t3 = st.text_area("Why did you choose this? (Tier 3 Reasoning):", placeholder="Enter your detailed reason here...")
            t4 = st.select_slider("Confidence (Reasoning):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            
            submit_btn = st.form_submit_button("Submit & Unlock Saathi AI")
            
            if submit_btn:
                if len(t3.strip()) < 5:
                    st.error("❌ Please provide a reasoning (Tier 3) to unlock the AI chatbot.")
                else:
                    # Log data
                    log_assessment(uid, group, active_row['Sub_Title'], t1, t2, t3, t4, "INITIAL", get_nepal_time())
                    
                    # THE BRIDGE: Lock module into session and force navigation
                    st.session_state.active_module = active_row.to_dict()
                    st.session_state.messages = [
                        {"role": "system", "content": SOCRATIC_NORMS},
                        {"role": "assistant", "content": f"I've reviewed your answer '{t1}' and your reasoning. Let's discuss it. Why do you think that specific mechanism occurs?"}
                    ]
                    st.session_state.current_tab = "🤖 Saathi AI"
                    st.rerun()
    else:
        st.success("All modules completed! Great job.")

# --- 3. UPDATED AI CHAT (Mastery Fixed) ---
def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if not module:
        st.warning("⚠️ Access Locked. Please submit your module answer first.")
        return

    # Split View: Question on Left, Chat on Right
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### 📝 Context")
        st.info(f"**Module:** {module['Sub_Title']}")
        st.write(f"**Q:** {module['Diagnostic_Question']}")
        st.write("---")
        st.caption("Your Tier 1/3 response has been shared with Saathi AI.")

    with col_right:
        if st.session_state.get('mastery_triggered'):
            st.balloons()
            render_tier_5_6(uid, group, module)
            return

        st.subheader("🤖 Chatting with Saathi AI")
        for m in st.session_state.messages[1:]:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Speak to Saathi..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
            ai_reply = resp.choices[0].message.content
            
            # CRITICAL: Mastery Detection Logic
            if "[MASTERY_DETECTED]" in ai_reply:
                st.session_state.mastery_triggered = True
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            log_temporal_trace(uid, "CHAT_MSG", f"Mod: {module['Sub_Title']} | {prompt}")
            st.rerun()

def render_tier_5_6(uid, group, module):
    st.success("🌟 Mastery Detected! Final Step:")
    st.info("Based on the discussion, provide your final conclusion.")
    with st.form("t56"):
        t5 = st.radio("Final Choice:", [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']])
        t6 = st.select_slider("Final Confidence:", ["Guessing", "Unsure", "Sure", "Very Sure"])
        if st.form_submit_button("Complete Module & Save Result"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", "Mastered", "N/A", "POST", 
                           get_nepal_time(), t5, t6)
            # Reset State
            st.session_state.active_module = None
            st.session_state.mastery_triggered = False
            st.session_state.messages = []
            st.session_state.current_tab = "🏠 Dashboard"
            st.rerun()

def render_progress(uid):
    st.header("📈 My Progress")
    st.write("Metacognitive growth data is being processed...")
