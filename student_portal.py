import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# Our research norms
SOCRATIC_NORMS = """
You are Saathi AI, a Socratic Chemistry Tutor.
1. NEVER give the student any sort of direct answer.
2. Ask one probing question at a time to uncover their mental model.
3. If they are wrong, point out a contradiction in their logic.
4. When they truly understand and explain correctly, output [MASTERY_DETECTED].
"""

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45))

def apply_modern_css():
    st.markdown("""
        <style>
        .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .stButton>button { background-color: #007bff; color: white; border-radius: 10px; font-weight: bold; }
        .bilingual-hint { color: #6c757d; font-size: 0.85rem; }
        </style>
    """, unsafe_allow_html=True)

def show():
    apply_modern_css()
    if 'user' not in st.session_state or st.session_state.user is None:
        st.stop()
        
    user = st.session_state.user
    uid, group = str(user.get('User_ID', '')).upper(), str(user.get('Group', 'Control'))

    # Bilingual Sidebar
    st.sidebar.markdown(f"### 🎓 {user.get('Name')}")
    menu = {
        "🏠 Dashboard": "ड्यासबोर्ड",
        "📚 Learning Modules": "सिकाई मोड्युलहरू",
        "🤖 Saathi AI": "साथी AI",
        "📈 My Progress": "मेरो प्रगति"
    }
    choice = st.sidebar.radio("Navigation / नेभिगेसन", list(menu.keys()), 
                              format_func=lambda x: f"{x} ({menu[x]})")

    if choice == "🏠 Dashboard": render_dashboard(user)
    elif choice == "📚 Learning Modules": render_modules(uid, group)
    elif choice == "🤖 Saathi AI": render_ai_chat(uid, group)
    elif choice == "📈 My Progress": render_progress(uid)

# Dashboard Design
def render_dashboard(user):
    now = get_nepal_time()
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.markdown("<p class='bilingual-hint'>Welcome to science learning portal / विज्ञान सिकाइ पोर्टलमा तपाईंलाई स्वागत छ।</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("🕒 Time", now.strftime("%I:%M %p"))
    with col2:
        st.metric("📅 Date", now.strftime("%b %d, %Y"))
    with col3:
        # 3D Image
        
        st.info("🎯**Our Goal:** 1) To enhance the understding of core concepts of science. 2) To enhance students' performance and engagement. 3) To increase learning outcomes.")
        st.info("🎯 **Our Plan:** 1) Consult Saathi AI for clear science concepts. 2) To complete diagnostic module for clear conceptual understandings.")
        st.info("🎯 **Our Appraoch:** 1) 24/7. 2) Personalized learning.")

# Modules(Tiers 1-4)
def render_modules(uid, group):
    st.header("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    
    m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    
    finished = logs_df[(logs_df['User_ID'].astype(str).str.upper() == uid) & (logs_df['Status'] == 'POST')]['Module_ID'].tolist()
    available = m_df[m_df['Group'].astype(str) == group]
    active = next((row for _, row in available.iterrows() if row['Sub_Title'] not in finished), None)

    if active is not None:
        st.subheader(f"📖 Module #{active.get('Module_No', '1')}: {active['Sub_Title']}")
        with st.container():
            with st.form("t14_form"):
                st.write(f"**Question / प्रश्न:** {active['Diagnostic_Question']}")
                opts = [active['Option_A'], active['Option_B'], active['Option_C'], active['Option_D']]
                t1 = st.radio("Choose Answer / उत्तर छान्नुहोस्:", opts)
                t2 = st.select_slider("Confidence / आत्मविश्वास:", ["Guessing", "Unsure", "Sure", "Very Sure"])
                t3 = st.text_area("Provide Reasoning / कारण दिनुहोस् (Tier 3):")
                t4 = st.select_slider("Reasoning Confidence:", ["Guessing", "Unsure", "Sure", "Very Sure"])
                
                if st.form_submit_button("Submit & Discuss with AI"):
                    log_assessment(uid, group, active['Sub_Title'], t1, t2, t3, t4, "INITIAL", get_nepal_time().strftime("%Y-%m-%d %H:%M"))
                    st.session_state.active_module = active
                    st.success("Logged! Please switch to Saathi AI tab.")
    else:
        st.balloons()
        st.success("All assigned modules complete! / सबै मोड्युलहरू पूरा भए!")

# --- PROGRESS VIEW (Restored & Aesthetic) ---
def render_progress(uid):
    st.header("📈 My Progress / मेरो प्रगति")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str).str.upper() == uid]

        if user_df.empty:
            st.warning("No data yet. Start a module to see progress cards.")
            return

        c1, c2, c3 = st.columns(3)
        m_started = len(user_df[user_df['Status'] == 'INITIAL'])
        m_done = len(user_df[user_df['Status'] == 'POST'])
        c1.metric("Started", m_started)
        c2.metric("Mastered", m_done)
        c3.metric("Growth Rate", f"{(m_done/m_started*100 if m_started>0 else 0):.0f}%")

        st.subheader("Confidence Growth Curve")
        # Visualizing metacognition as requested for PhD analysis
        fig = px.area(user_df, x="Timestamp", y="Tier_2 (Confidence_Ans)", 
                      title="Confidence Trend / आत्मविश्वास प्रवृत्ति", 
                      labels={"Tier_2 (Confidence_Ans)": "Confidence Level"})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Progress data error: {e}")

# --- SAATHI AI VIEW (Socratic Value) ---
def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if not module:
        st.warning("Please submit an initial answer in 'Learning Modules' first.")
        return

    st.subheader(f"🤖 Socratic Dialogue: {module['Sub_Title']}")
    
    if st.session_state.get('mastery_detected'):
        render_final_t5_t6(uid, group, module)
        return

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SOCRATIC_NORMS}]

    for m in st.session_state.messages[1:]:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic to Saathi..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_temporal_trace(uid, "CHAT_MSG", f"Mod: {module['Sub_Title']} | {prompt}")
        
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        reply = resp.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in reply:
            st.session_state.mastery_detected = True
            st.rerun()
            
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

def render_final_t5_t6(uid, group, module):
    st.success("🌟 Mastery Detected! Final Step / अन्तिम चरण")
    
    with st.form("t56_final"):
        st.markdown("### Post-Discussion Assessment (Tier 5 & 6)")
        opts = [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']]
        t5 = st.radio("Revised Choice:", opts)
        t6 = st.select_slider("Revised Confidence:", ["Guessing", "Unsure", "Sure", "Very Sure"])
        
        if st.form_submit_button("Complete Module"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", "Mastered", "N/A", "POST", 
                           get_nepal_time().strftime("%Y-%m-%d %H:%M"), t5, t6)
            del st.session_state.active_module
            st.session_state.mastery_detected = False
            st.rerun()
