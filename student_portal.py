import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace, fetch_chat_history
from datetime import datetime, timedelta

# --- 1. RESEARCH HELPERS ---
def get_nepal_time():
    utc_now = datetime.utcnow()
    nepal_now = utc_now + timedelta(hours=5, minutes=45)
    return nepal_now

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.stop()
        
    user = st.session_state.user
    uid = str(user.get('User_ID', '')).strip().upper()
    group = str(user.get('Group', 'Control')).strip()

    # SIDEBAR NAVIGATION
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = {"🏠 Dashboard": "🏠 ड्यासबोर्ड", "📚 Learning Modules": "📚 मोड्युलहरू", 
            "🤖 Saathi AI": "🤖 साथी AI", "📈 My Progress": "📈 प्रगति"}
    
    choice = st.sidebar.radio("Navigation", list(menu.keys()), 
                              format_func=lambda x: f"{x} ({menu[x]})")

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(uid, group)
    elif choice == "🤖 Saathi AI":
        render_ai_chat(uid, group)
    elif choice == "📈 My Progress":
        render_progress(uid)

# --- 2. DASHBOARD (Visuals, Watch, Calendar) ---
def render_dashboard(user):
    now = get_nepal_time()
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🕒 Real-Time Session Status")
        m1, m2 = st.columns(2)
        m1.metric("Local Watch (NP)", now.strftime("%H:%M:%S"))
        
        # Calendar logic
        eng_date = now.strftime("%A, %d %B %Y")
        # Placeholder for Nepali conversion logic
        nep_date = "२०८० फागुन १६ गते (BS)" 
        m2.info(f"📅 **English:** {eng_date}\n\n📅 **नेपाली:** {nep_date}")
        
        st.success("🎯 **Goal:** Complete your active module to contribute to the research study.")

    with col2:
        st.markdown("### ⚛️ Atomic Visualization")
        # 3D Placeholder (GIF or Link to interactive)
        st.image("https://upload.wikimedia.org/wikipedia/commons/e/e1/Stylised_Lithium_Atom.png", 
                 caption="Conceptual 3D Model")

# --- 3. MODULE SELECTION (Fixing Numbering) ---
def render_modules(uid, group):
    st.header("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    
    # Check completed modules
    logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    finished = []
    if not logs.empty:
        finished = logs[(logs['User_ID'].astype(str).str.upper() == uid) & 
                        (logs['Status'] == 'POST')]['Module_ID'].tolist()

    m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    available = m_df[m_df['Group'].astype(str) == group]
    
    # Get next available module
    active = next((row for _, row in available.iterrows() if row['Sub_Title'] not in finished), None)

    if active is not None:
        # FIX: Explicitly show Module Number
        m_num = active.get('Module_No', 'N/A')
        st.subheader(f"📖 Module #{m_num}: {active['Sub_Title']}")
        
        with st.form("tier1_4"):
            st.write(f"**Diagnostic Question:** {active['Diagnostic_Question']}")
            t1 = st.radio("Answer:", [active['Option_A'], active['Option_B'], active['Option_C'], active['Option_D']])
            t2 = st.select_slider("Confidence:", ["Guessing", "Unsure", "Sure", "Very Sure"])
            t3 = st.text_area("Reasoning:")
            t4 = st.select_slider("Reasoning Confidence:", ["Guessing", "Unsure", "Sure", "Very Sure"])
            
            if st.form_submit_button("Start Socratic Discussion"):
                st.session_state.active_module = active
                log_assessment(uid, group, active['Sub_Title'], t1, t2, t3, t4, "INITIAL", get_nepal_time().strftime("%Y-%m-%d %H:%M"))
                st.info("Assessment saved. Go to 'Saathi AI' to discuss.")
    else:
        st.balloons()
        st.success("Congratulations! All modules for your group are complete.")

# --- 4. SAATHI AI (Persistence & Mastery T5/T6) ---
def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if module is None:
        st.warning("Please select a module in the 'Learning Modules' tab first.")
        return

    st.subheader(f"🤖 Discussing: {module['Sub_Title']}")

    # Mastery Logic: Tier 5 & 6
    if st.session_state.get('mastery_triggered'):
        render_final_revision(uid, group, module)
        return

    # CHAT HISTORY RECOVERY (Research Feature)
    if "messages" not in st.session_state:
        # Try to fetch from DB first
        history = fetch_chat_history(uid, module['Sub_Title'])
        if history:
            st.session_state.messages = [{"role": "system", "content": "You are Saathi AI..."}] + history
        else:
            st.session_state.messages = [{"role": "system", "content": f"You are Saathi, a Socratic Tutor for Chemistry. Topic: {module['Sub_Title']}. Guide the student. If they show mastery, say [MASTERY_DETECTED]."}]

    for m in st.session_state.messages[1:]:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        # PERSIST TO DB IMMEDIATELY
        log_temporal_trace(uid, "CHAT_MSG", f"Topic: {module['Sub_Title']} | Content: {prompt}")
        
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        ai_reply = resp.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state.mastery_triggered = True
            st.rerun()

        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        st.rerun()

def render_final_revision(uid, group, module):
    st.success("🌟 Mastery Detected! Final Step:")
    st.info("Based on your dialogue with Saathi AI, provide your final conclusion.")
    
    with st.form("tier5_6"):
        t5 = st.radio("Revised Choice (Tier 5):", [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']])
        t6 = st.select_slider("Revised Confidence (Tier 6):", ["Guessing", "Unsure", "Sure", "Very Sure"])
        
        if st.form_submit_button("Complete Module"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", "Mastered via AI", "N/A", "POST", 
                           get_nepal_time().strftime("%Y-%m-%d %H:%M"), t5, t6)
            
            # Clear state for next module
            del st.session_state.active_module
            del st.session_state.messages
            st.session_state.mastery_triggered = False
            st.success("Data recorded. Moving to the next concept.")
            st.rerun()

def render_progress(uid):
    st.title("📈 My Progress")
    # Existing progress logic from your repo goes here...
