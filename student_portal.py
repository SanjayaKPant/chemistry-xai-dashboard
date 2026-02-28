import streamlit as st
import pandas as pd
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- RESEARCH CONSTANTS ---
SOCRATIC_NORMS = """
You are Saathi AI, a Socratic Chemistry Tutor. 
1. NEVER give the student the answer. 
2. Use the question provided in context to guide them.
3. If they understand, output [MASTERY_DETECTED].
"""

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45))

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.stop()
        
    user = st.session_state.user
    uid, group = str(user.get('User_ID', '')).upper(), str(user.get('Group', 'Control'))

    # SIDEBAR NAVIGATION
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Saathi AI", "📈 My Progress"]
    
    # Initialize navigation state if not present
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "🏠 Dashboard"

    # Sync the sidebar radio with the session state
    choice = st.sidebar.radio("Navigation", menu, 
                              index=menu.index(st.session_state.current_tab),
                              key="nav_radio")
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard": render_dashboard(user)
    elif choice == "📚 Learning Modules": render_modules(uid, group)
    elif choice == "🤖 Saathi AI": render_ai_chat(uid, group)
    elif choice == "📈 My Progress": render_progress(uid)

def render_dashboard(user):
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.info("Goal: Complete the diagnostic questions and discuss your reasoning with Saathi AI.")

def render_modules(uid, group):
    st.header("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    
    finished = logs_df[(logs_df['User_ID'].astype(str).str.upper() == uid) & (logs_df['Status'] == 'POST')]['Module_ID'].tolist()
    active_row = m_df[~m_df['Sub_Title'].isin(finished)].iloc[0] if not m_df[~m_df['Sub_Title'].isin(finished)].empty else None

    if active_row is not None:
        with st.form("t14_form"):
            st.subheader(active_row['Sub_Title'])
            st.write(f"**Question:** {active_row['Diagnostic_Question']}")
            t1 = st.radio("Answer:", [active_row['Option_A'], active_row['Option_B'], active_row['Option_C'], active_row['Option_D']])
            t2 = st.select_slider("Confidence (Ans):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            t3 = st.text_area("Reasoning (Tier 3):")
            t4 = st.select_slider("Confidence (Reasoning):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            
            if st.form_submit_button("Submit & Start Discussion"):
                if len(t3.strip()) < 5:
                    st.error("Please provide a reason.")
                else:
                    log_assessment(uid, group, active_row['Sub_Title'], t1, t2, t3, t4, "INITIAL", get_nepal_time().strftime("%Y-%m-%d %H:%M"))
                    # Store module as dict for the Chat tab
                    st.session_state.active_module = active_row.to_dict()
                    # REDIRECT LOGIC: Change the tab state and rerun
                    st.session_state.current_tab = "🤖 Saathi AI"
                    st.rerun()

# --- 3. SAATHI AI (Fixed Layout: Question on Side) ---
def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if not module:
        st.warning("Please complete a module question first.")
        return

    # Split screen: Question on left, Chat on right
    col_q, col_c = st.columns([1, 2])

    with col_q:
        st.markdown("### 📝 Current Question")
        st.info(f"**Topic:** {module['Sub_Title']}\n\n**Q:** {module['Diagnostic_Question']}")
        st.write("---")
        st.write(f"A) {module['Option_A']}\n\nB) {module['Option_B']}\n\nC) {module['Option_C']}\n\nD) {module['Option_D']}")

    with col_c:
        st.subheader("🤖 Chat with Saathi AI")
        if st.session_state.get('mastery_triggered'):
            st.success("Mastery detected! Please finalize your answer below.")
            render_tier_5_6(uid, group, module)
            return

        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "system", "content": SOCRATIC_NORMS}]

        for m in st.session_state.messages[1:]:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Explain your logic..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
            reply = resp.choices[0].message.content
            
            if "[MASTERY_DETECTED]" in reply:
                st.session_state.mastery_triggered = True
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

def render_tier_5_6(uid, group, module):
    with st.form("t56"):
        t5 = st.radio("Final Choice:", [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']])
        t6 = st.select_slider("Final Confidence:", ["Guessing", "Unsure", "Sure", "Very Sure"])
        if st.form_submit_button("Complete Module"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", "Mastered", "N/A", "POST", 
                           get_nepal_time().strftime("%Y-%m-%d %H:%M"), t5, t6)
            st.session_state.active_module = None
            st.session_state.mastery_triggered = False
            st.session_state.messages = []
            st.session_state.current_tab = "🏠 Dashboard"
            st.rerun()

def render_progress(uid):
    st.header("📈 Progress Tracking")
