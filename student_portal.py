import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace, fetch_chat_history
from datetime import datetime, timedelta

# --- 1. GLOBAL HELPERS ---
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

    # SIDEBAR
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = {"🏠 Dashboard": "🏠 ड्यासबोर्ड", "📚 Learning Modules": "📚 मोड्युलहरू", 
            "🤖 Saathi AI": "🤖 साथी AI", "📈 My Progress": "📈 मेरो प्रगति"}
    
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

# --- 2. THE DASHBOARD ---
def render_dashboard(user):
    now = get_nepal_time()
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    
    col_main, col_visual = st.columns([2, 1])
    
    with col_main:
        st.markdown("### 🕒 Real-Time Research Status")
        c1, c2 = st.columns(2)
        c1.metric("Local Watch (Nepal)", now.strftime("%I:%M:%P"))
        
        eng_date = now.strftime("%B %d, %Y")
        # BS Date placeholder (Researcher to update with conversion logic if needed)
        c2.info(f"📅 **English:** {eng_date}\n\n📅 **नेपाली:** २०८० फागुन १६ गते")
        
        st.success("🎯 **Research Goal:** Complete the Socratic dialogue to unlock your revised assessment.")

    with col_visual:
        st.markdown("### ⚛️ Atomic Model")
        st.image("https://upload.wikimedia.org/wikipedia/commons/e/e1/Stylised_Lithium_Atom.png", 
                 caption="Conceptual Visualization")

# --- 3. MODULES & TIER 1-4 ---
def render_modules(uid, group):
    st.header("📚 Active Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    
    # Filter out completed modules (POST status)
    logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    finished = []
    if not logs.empty:
        finished = logs[(logs['User_ID'].astype(str).str.upper() == uid) & 
                        (logs['Status'] == 'POST')]['Module_ID'].tolist()

    m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    available = m_df[m_df['Group'].astype(str) == group]
    
    # Find first module not yet mastered
    active_module = next((row for _, row in available.iterrows() if row['Sub_Title'] not in finished), None)

    if active_module:
        m_num = active_module.get('Module_No', '1')
        st.subheader(f"📖 Module #{m_num}: {active_module['Sub_Title']}")
        
        with st.form("tier1_4_form"):
            st.info(f"**Diagnostic Question:** {active_module['Diagnostic_Question']}")
            t1 = st.radio("Choose your answer:", [active_module['Option_A'], active_module['Option_B'], active_module['Option_C'], active_module['Option_D']])
            t2 = st.select_slider("Confidence (Tier 2):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            t3 = st.text_area("Why did you choose this? (Tier 3 Reasoning):")
            t4 = st.select_slider("Reasoning Confidence (Tier 4):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            
            if st.form_submit_button("Submit & Start AI Discussion"):
                st.session_state.active_module = active_module
                log_assessment(uid, group, active_module['Sub_Title'], t1, t2, t3, t4, "INITIAL", get_nepal_time().strftime("%Y-%m-%d %H:%M"))
                st.success("Initial Assessment Logged! Please go to '🤖 Saathi AI' tab.")
    else:
        st.balloons()
        st.success("All assigned modules are complete!")

# --- 4. SAATHI AI & TIER 5-6 ---
def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if not module:
        st.warning("Please select a module in 'Learning Modules' first.")
        return

    st.subheader(f"🤖 Socratic Dialogue: {module['Sub_Title']}")

    # Check if AI has already detected mastery
    if st.session_state.get('mastery_detected'):
        render_final_tier(uid, group, module)
        return

    # Chat logic
    if "messages" not in st.session_state:
        history = fetch_chat_history(uid, module['Sub_Title'])
        if history:
            st.session_state.messages = [{"role": "system", "content": "Socratic Tutor..."}] + history
        else:
            st.session_state.messages = [{"role": "system", "content": f"You are Saathi. Use Socratic questioning for: {module['Sub_Title']}. When you detect the student has correct mental models, include [MASTERY_DETECTED]."}]

    for m in st.session_state.messages[1:]:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic to Saathi..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_temporal_trace(uid, "CHAT_MSG", f"Module: {module['Sub_Title']} | Content: {prompt}")

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        ai_reply = resp.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state.mastery_detected = True
            st.rerun()

        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        st.rerun()

def render_final_tier(uid, group, module):
    """Captures Tier 5 and 6: The Conceptual Change outcome."""
    st.success("🌟 Mastery Detected! Final Step.")
    st.markdown("### Revised Assessment | परिमार्जित मूल्यांकन")
    
        
    with st.form("tier5_6_form"):
        t5 = st.radio("Revised Answer (Tier 5):", [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']])
        t6 = st.select_slider("Revised Confidence (Tier 6):", ["Guessing", "Unsure", "Sure", "Very Sure"])
        
        if st.form_submit_button("Complete & Save Final Data"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", "Mastered", "N/A", "POST", 
                           get_nepal_time().strftime("%Y-%m-%d %H:%M"), t5, t6)
            
            # Reset session for next module
            del st.session_state.active_module
            del st.session_state.messages
            st.session_state.mastery_detected = False
            st.success("Module Completed! Select a new one from the list.")
            st.rerun()

def render_progress(uid):
    st.title("📈 My Research Progress")
    # (Existing progress visualization code goes here)
