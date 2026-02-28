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

    # SIDEBAR
    st.sidebar.markdown(f"### 🎓 {user.get('Name')}")
    menu = {
        "🏠 Dashboard": "🏠 ड्यासबोर्ड",
        "📚 Learning Modules": "📚 सिकाई मोड्युलहरू",
        "🤖 Saathi AI": "🤖 साथी AI",
        "📈 My Progress": "📈 मेरो प्रगति"
    }
    
    # Initialize navigation if not exists
    if "current_nav" not in st.session_state:
        st.session_state.current_nav = "🏠 Dashboard"

    # Navigation Radio
    choice = st.sidebar.radio("Navigation", list(menu.keys()), 
                              index=list(menu.keys()).index(st.session_state.current_nav),
                              format_func=lambda x: f"{x} ({menu[x]})",
                              key="nav_radio")
    
    # Update current nav based on radio selection
    st.session_state.current_nav = choice

    if st.session_state.current_nav == "🏠 Dashboard": render_dashboard(user)
    elif st.session_state.current_nav == "📚 Learning Modules": render_modules(uid, group)
    elif st.session_state.current_nav == "🤖 Saathi AI": render_ai_chat(uid, group)
    elif st.session_state.current_nav == "📈 My Progress": render_progress(uid)

def render_dashboard(user):
    now = get_nepal_time()
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("🕒 Nepal Time", now.strftime("%I:%M %p"))
    with col2:
        st.metric("📅 Date", now.strftime("%b %d, %Y"))
    with col3:
        st.image("https://upload.wikimedia.org/wikipedia/commons/e/e1/Stylised_Lithium_Atom.png", width=120)

    st.info("🎯 **Goal:** Complete your modules and engage in Socratic dialogue to master concepts.")

def render_modules(uid, group):
    st.header("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    
    m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
    
    finished = logs_df[(logs_df['User_ID'].astype(str).str.upper() == uid) & (logs_df['Status'] == 'POST')]['Module_ID'].tolist()
    available = m_df[m_df['Group'].astype(str) == group]
    
    active = None
    for _, row in available.iterrows():
        if row['Sub_Title'] not in finished:
            active = row
            break

    if active is not None:
        st.subheader(f"📖 {active['Sub_Title']}")
        with st.form("t14_form"):
            st.write(f"**Question:** {active['Diagnostic_Question']}")
            opts = [active['Option_A'], active['Option_B'], active['Option_C'], active['Option_D']]
            t1 = st.radio("Choose Answer:", opts)
            t2 = st.select_slider("Confidence in Answer:", ["Guessing", "Unsure", "Sure", "Very Sure"])
            t3 = st.text_area("Provide Reasoning (Tier 3):")
            t4 = st.select_slider("Confidence in Reasoning (Tier 4):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            
            if st.form_submit_button("Submit & Start Discussion"):
                if not t3 or len(t3.strip()) < 5:
                    st.error("❌ Please provide a reason (Tier 3) to continue.")
                else:
                    log_assessment(uid, group, active['Sub_Title'], t1, t2, t3, t4, "INITIAL", get_nepal_time().strftime("%Y-%m-%d %H:%M"))
                    st.session_state.active_module = active.to_dict()
                    
                    # FIXED: Instead of st.switch_page, we update the navigation state
                    st.session_state.current_nav = "🤖 Saathi AI"
                    st.success("Logged! Redirecting to Saathi AI...")
                    st.rerun()
    else:
        st.success("All modules completed!")

def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if module is None:
        st.warning("Please complete a module question first.")
        return

    if st.session_state.get('mastery_triggered'):
        render_tier_5_6_form(uid, group, module)
        return

    st.subheader(f"🤖 Discussion: {module['Sub_Title']}")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SOCRATIC_NORMS}]

    for m in st.session_state.messages[1:]:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
            ai_msg = resp.choices[0].message.content
            
            log_temporal_trace(uid, "CHAT_LOG", f"Topic: {module['Sub_Title']} | Msg: {prompt}")

            if "[MASTERY_DETECTED]" in ai_msg:
                st.session_state.mastery_triggered = True
                st.rerun()

            st.session_state.messages.append({"role": "assistant", "content": ai_msg})
            st.rerun()
        except Exception as e:
            st.error(f"AI Error: {e}")

def render_tier_5_6_form(uid, group, module):
    st.success("🌟 Mastery Detected! Final Step:")
    st.info("Based on your discussion, would you like to keep or change your original answer? / साथी एआईसँगको छलफलको आधारमा, के तपाईं आफ्नो अघिल्लो उत्तर राख्न वा परिमार्जन गर्न चाहनुहुन्छ?")
    
    with st.form("tier5_6"):
        t5 = st.radio("Final Answer (Tier 5):", [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']])
        t6 = st.select_slider("Final Confidence (Tier 6):", ["Guessing", "Unsure", "Sure", "Very Sure"])
        
        if st.form_submit_button("Confirm Mastery & Save"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", "Mastered via Chat", "N/A", "POST", 
                           get_nepal_time().strftime("%Y-%m-%d %H:%M"), t5, t6)
            st.session_state.active_module = None
            st.session_state.mastery_triggered = False
            st.session_state.messages = []
            st.session_state.current_nav = "🏠 Dashboard"
            st.rerun()

def render_progress(uid):
    st.header("📈 My Progress")
    st.write("Tracking your conceptual growth...")
