import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- 1. RESEARCH HELPERS (NEPAL TIME) ---
def get_nepal_time():
    """VPS Requirement: Precise timestamping for Nepal-based research."""
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

# --- 3. MODULES (WITH COMPLETION LOGIC) ---
def render_modules(uid, group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Fetch existing logs to see what is already finished
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        # Filter for current user and modules marked as "POST" (Completed)
        finished_modules = []
        if not log_df.empty:
            finished_modules = log_df[(log_df['User_ID'].astype(str) == str(uid)) & (log_df['Status'] == 'POST')]['Module_ID'].tolist()

        # Fetch available modules
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        all_modules = df[df['Group'] == group]

        if all_modules.empty:
            st.warning("तपाईंको समूहको लागि कुनै मोड्युलहरू छैनन्।")
            return

        # Sequential Logic: Show only the first module that isn't finished
        active_module = None
        for idx, row in all_modules.iterrows():
            if row['Sub_Title'] not in finished_modules:
                active_module = row
                break # Stop at the first uncompleted module

        if active_module is None:
            st.success("🎉 बधाई छ! तपाईंले यो समूहका सबै मोड्युलहरू पूरा गर्नुभयो।")
            st.balloons()
            return

        m_id = active_module['Sub_Title']
        st.subheader(f"📖 {m_id}")
        
        # Display Objectives and Materials (Restored from your earlier requests)
        with st.expander("Learning Objectives & Materials", expanded=True):
            st.write(f"**Objectives:** {active_module.get('Objectives', 'Learn the core concepts.')}")
            if active_module.get('File_Link'):
                st.markdown(f"[📄 Download Study Material]({active_module['File_Link']})")

        # REVISION MODE (Tiers 5 & 6)
        if st.session_state.get(f"mastery_{m_id}"):
            st.success("🎯 साथी AI: 'तपाईंको बुझाइ अब प्रष्ट भएको छ। कृपया अन्तिम उत्तर दिनुहोस्।'")
            t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{m_id}")
            t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Final Confidence)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{m_id}")
            
            if st.button("Complete Module & Move to Next", key=f"fbtn_{m_id}"):
                log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", "POST", get_nepal_time(), t5, t6, "Corrected", "Resolved")
                st.session_state[f"mastery_{m_id}"] = False
                st.session_state.ai_session_active = False
                st.success(f"मोड्युल {m_id} पूरा भयो! अब अर्को मोड्युल लोड हुँदैछ...")
                st.rerun()
        
        # INITIAL MODE (Tiers 1-4)
        else:
            st.write(f"**Diagnostic Question:** {active_module['Diagnostic_Question']}")
            t1 = st.radio("सही उत्तर छान्नुहोस् (Tier 1)", [active_module['Option_A'], active_module['Option_B'], active_module['Option_C'], active_module['Option_D']], key=f"t1_{m_id}")
            t2 = st.select_slider("आत्मविश्वास (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{m_id}")
            t3 = st.text_area("तपाईंको वैज्ञानिक तर्क (Tier 3 Reasoning)", key=f"t3_{m_id}")
            t4 = st.select_slider("तर्कमा आत्मविश्वास (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{m_id}")

            if st.button("Submit & Start AI Discussion", key=f"btn_{m_id}"):
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                st.session_state.current_topic = m_id
                st.session_state.initial_ans = t1
                st.session_state.initial_reasoning = t3
                st.session_state.logic_tree = active_module['Socratic_Tree']
                st.session_state.ai_session_active = True
                st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

# --- 4. SAATHI AI (LOCALIZED & SOCRATIC) ---
def render_ai_chat(uid, group):
    st.title("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic')
    
    if not topic:
        st.warning("मोड्युलमा गएर पहिले प्रश्नको उत्तर दिनुहोस्।")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"""
            You are 'Saathi AI', a polite Socratic tutor for high school students in Nepal.
            OBJECTIVE: Use the Socratic method to lead the student to: {st.session_state.get('logic_tree')}.
            STUDENT CONTEXT: They chose '{st.session_state.get('initial_ans')}' because: '{st.session_state.get('initial_reasoning')}'.
            CONSTRAINTS:
            1. Language: Simple English. Understand Nepali/Roman Nepali.
            2. Short sentences (max 3). Ask probing questions.
            3. EXIT: When they explain it correctly, say: 'बधाई छ! तपाईंको बुझाइ प्रष्ट भयो। [MASTERY_DETECTED]'
        """}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("साथी AI सँग कुरा गर्नुहोस्..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.session_state.current_tab = "📚 Learning Modules"
            st.rerun()
        
        st.chat_message("assistant").markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        log_temporal_trace(uid, "CHAT", f"S: {prompt} | AI: {ai_reply[:50]}")

# --- 5. PROGRESS (PhD VISUALIZATION) ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress)")
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, label=["Guessing", "Sure", "Post-Unsure", "Mastery"]),
        link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[2, 8, 5, 1])
    )])
    st.plotly_chart(fig, use_container_width=True)
