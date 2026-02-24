import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- 1. RESEARCH HELPERS (NEPAL TIME) ---
def get_nepal_time():
    """VPS Requirement: Precise timestamping for Nepal-based research (UTC +5:45)."""
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first)")
        st.stop()
        
    user = st.session_state.user
    uid = user.get('User_ID')
    group = str(user.get('Group', 'School A')).strip()

    # SIDEBAR NAVIGATION
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {group}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    
    # Persistent tab state for automatic redirection
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = menu[0]

    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_tab))
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(uid, group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid, group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)

# --- 2. DASHBOARD ---
def render_dashboard(user):
    st.title(f"नमस्ते, {user['Name']}! 🙏")
    st.markdown("### साथी (Saathi) AI सिकाई पोर्टल")
    st.info("तपाईंको आजको लक्ष्य: मोड्युल पूरा गर्नुहोस् र साथी AI सँग छलफल गर्नुहोस्।")
    

# --- 3. MODULES (WITH SEQUENTIAL LOCKING) ---
def render_modules(uid, group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # 1. Fetch existing logs to check for finished modules
        log_ws = sh.worksheet("Assessment_Logs")
        log_df = pd.DataFrame(log_ws.get_all_records())
        
        finished_modules = []
        if not log_df.empty and 'Status' in log_df.columns:
            # Module is considered finished if there is a 'POST' entry for this user
            finished_modules = log_df[(log_df['User_ID'].astype(str) == str(uid)) & (log_df['Status'] == 'POST')]['Module_ID'].tolist()

        # 2. Fetch available modules from Instructional Materials
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        all_modules = df[df['Group'] == group]

        if all_modules.empty:
            st.warning("तपाईंको समूहको लागि कुनै मोड्युलहरू छैनन्।")
            return

        # 3. SEQUENTIAL LOGIC: Find the FIRST module that is NOT finished
        active_module = None
        for _, row in all_modules.iterrows():
            if row['Sub_Title'] not in finished_modules:
                active_module = row
                break 

        if active_module is None:
            st.success("🎉 बधाई छ! तपाईंले सबै मोड्युलहरू पूरा गर्नुभयो।")
            st.balloons()
            return

        m_id = active_module['Sub_Title']
        st.subheader(f"📖 {m_id}")
        
        with st.expander("Learning Objectives & Materials", expanded=True):
            st.write(f"**Objectives:** {active_module.get('Objectives', 'N/A')}")
            if active_module.get('File_Link'):
                st.markdown(f"[📄 Download Study Material]({active_module['File_Link']})")

        # REVISION MODE (Tiers 5 & 6) - Unlocked by Saathi AI
        if st.session_state.get(f"mastery_{m_id}"):
            st.success("🎯 साथी AI ले तपाईंको बुझाइ सुधार भएको पुष्टि गरेको छ।")
            t5 = st.text_area("Tier 5: परिमार्जित तर्क (Revised Reasoning)", key=f"t5_{m_id}")
            t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Final Confidence)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{m_id}")
            
            if st.button("Complete Module & Move to Next", key=f"fbtn_{m_id}"):
                # Log using the updated 12-column logic
                log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", "POST", get_nepal_time(), t5, t6, "Corrected", "Resolved")
                st.session_state[f"mastery_{m_id}"] = False
                st.session_state.ai_session_active = False
                st.success(f"मोड्युल {m_id} पूरा भयो!")
                st.rerun()
        
        # INITIAL MODE (Tiers 1-4)
        else:
            st.write(f"**Diagnostic Question:** {active_module['Diagnostic_Question']}")
            t1 = st.radio("उत्तर (Tier 1)", [active_module['Option_A'], active_module['Option_B'], active_module['Option_C'], active_module['Option_D']], key=f"t1_{m_id}")
            t2 = st.select_slider("उत्तरमा आत्मविश्वास (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{m_id}")
            t3 = st.text_area("तपाईंको तर्क (Tier 3 Reasoning)", key=f"t3_{m_id}")
            t4 = st.select_slider("तर्कमा आत्मविश्वास (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{m_id}")

            if st.button("Submit & Start AI Discussion", key=f"btn_{m_id}"):
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                st.session_state.current_topic = m_id
                st.session_state.initial_ans = t1
                st.session_state.initial_reasoning = t3
                st.session_state.logic_tree = active_module['Socratic_Tree']
                st.session_state.ai_session_active = True
                
                # REDIRECT TO AI TAB
                st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

# --- 4. SAATHI AI (THE SOCRATIC INTERVENTION) ---
def render_ai_chat(uid, group):
    st.title("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic')
    
    if not topic:
        st.warning("पहिले मोड्युलमा गएर उत्तर दिनुहोस्।")
        return

    st.info(f"हामी **{topic}** को बारेमा छलफल गर्दैछौं।")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"""
            You are 'Saathi AI', a polite Socratic tutor for high school students in Nepal.
            OBJECTIVE: Lead the student to: {st.session_state.get('logic_tree')}.
            STUDENT ANSWER: They chose '{st.session_state.get('initial_ans')}' because: '{st.session_state.get('initial_reasoning')}'.
            CONSTRAINTS:
            - Understand Nepali and Roman Nepali (e.g., 'Mero logic thik cha?').
            - Use simple English. Short responses (max 3 sentences).
            - NEVER give the answer. Use probing questions.
            - EXIT: When the student explains the concept scientifically, say: 
              'तपाईंको बुझाइ प्रष्ट भयो! अब मोड्युलमा गएर आफ्नो उत्तर परिमार्जन गर्नुहोस्। [MASTERY_DETECTED]'
        """}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("साथी AI सँग कुरा गर्नुहोस्..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.success("🎯 Mastery detected! Redirecting back to Learning Modules...")
            st.session_state.current_tab = "📚 Learning Modules"
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
        
        with st.chat_message("assistant"): st.markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        log_temporal_trace(uid, "CHAT", f"S: {prompt} | AI: {ai_reply[:50]}")

# --- 5. PROGRESS ANALYTICS ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress)")
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15,
