import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- 1. GLOBAL RESEARCH HELPERS ---
def get_nepal_time():
    """VPS Requirement: Precise timestamping for UTC +5:45."""
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("Please login first | कृपया पहिले लगइन गर्नुहोस्")
        st.stop()
        
    user = st.session_state.user
    uid = str(user.get('User_ID', '')).strip().upper()
    group = str(user.get('Group', 'Control')).strip()

    # Bilingual Sidebar
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.write(f"**ID:** {uid} | **Group:** {group}")
    
    menu = {
        "🏠 Dashboard": "🏠 ड्यासबोर्ड",
        "📚 Learning Modules": "📚 सिकाई मोड्युलहरू",
        "🤖 Saathi AI": "🤖 साथी AI",
        "📈 My Progress": "📈 मेरो प्रगति"
    }
    
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = list(menu.keys())[0]

    choice = st.sidebar.radio("Navigation", list(menu.keys()), 
                              format_func=lambda x: f"{x} ({menu[x]})",
                              index=list(menu.keys()).index(st.session_state.current_tab))
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(uid, group)
    elif choice == "🤖 Saathi AI":
        render_ai_chat(uid, group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)

# --- 2. MODULE ENGINE (Fixed Visibility & Numbering) ---
def render_modules(uid, group):
    st.header("Learning Modules | सिकाई मोड्युलहरू")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # 1. Get student logs - Fixed filtering logic
        all_logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        finished = []
        if not all_logs.empty:
            all_logs['User_ID'] = all_logs['User_ID'].astype(str).str.strip().str.upper()
            finished = all_logs[(all_logs['User_ID'] == uid) & (all_logs['Status'] == 'POST')]['Module_ID'].tolist()

        # 2. Get materials filtered by Group
        m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        # Ensure group matching is clean
        available = m_df[m_df['Group'].astype(str).str.strip() == group]

        # 3. Find next module
        active_module = next((row for _, row in available.iterrows() if row['Sub_Title'] not in finished), None)

        if active_module is None:
            st.success("🎉 All modules completed! | सबै मोड्युलहरू पूरा भए!")
            return

        # Display numbering (Assumes Column 'Module_No' exists in Sheet)
        m_no = active_module.get('Module_No', '1')
        m_id = active_module['Sub_Title']
        st.subheader(f"📖 Module {m_no}: {m_id}")

        # Diagnostic UI
        st.info(f"**Question:** {active_module['Diagnostic_Question']}")
        t1 = st.radio("Select Answer:", [active_module['Option_A'], active_module['Option_B'], active_module['Option_C'], active_module['Option_D']])
        t2 = st.select_slider("Confidence (Tier 2):", ["Guessing", "Unsure", "Sure", "Very Sure"])
        t3 = st.text_area("Reasoning (Tier 3):")
        t4 = st.select_slider("Reasoning Confidence (Tier 4):", ["Guessing", "Unsure", "Sure", "Very Sure"])

        if st.button("Submit & Start AI Discussion"):
            # Save module data to session for the Chat Tab
            st.session_state.current_topic = m_id
            st.session_state.active_module_data = active_module
            
            # Log Initial Assessment
            log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
            st.session_state.current_tab = "🤖 Saathi AI"
            st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# --- 3. SAATHI AI (Fixed Logging & KeyErrors) ---
def render_ai_chat(uid, group):
    topic = st.session_state.get('current_topic')
    module_data = st.session_state.get('active_module_data')

    if not topic or module_data is None:
        st.warning("Please complete the diagnostic module first.")
        return

    col_ref, col_chat = st.columns([1, 2])
    
    with col_ref:
        st.markdown("### 📍 Reference Context")
        st.write(f"**Topic:** {topic}")
        st.caption(module_data.get('Diagnostic_Question', ''))
        # Safe link retrieval
        link = module_data.get('File_Link')
        if pd.notna(link) and str(link).startswith("http"):
            st.link_button("📄 View Material", str(link))

    with col_chat:
        if "messages" not in st.session_state:
            logic = module_data.get('Socratic_Tree', 'Use Socratic questioning.')
            st.session_state.messages = [{"role": "system", "content": f"You are Saathi, a Socratic Chemistry Tutor. Focus: {logic}. Support Nepali and English. Use [MASTERY_DETECTED] when they understand."}]

        for m in st.session_state.messages:
            if m["role"] != "system":
                with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Ask Saathi AI..."):
            with st.chat_message("user"): st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
            ai_reply = response.choices[0].message.content
            
            # RECTIFIED: Detailed chat logging for PhD Trace Analysis
            trace_detail = f"User: {prompt} | Saathi: {ai_reply}"
            log_temporal_trace(uid, f"CHAT_{topic}", trace_detail)

            if "[MASTERY_DETECTED]" in ai_reply:
                st.session_state[f"mastery_{topic}"] = True
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                st.success("Mastery Detected! Returning to module...")
                st.session_state.current_tab = "📚 Learning Modules"
                st.rerun()

            with st.chat_message("assistant"): st.markdown(ai_reply)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})

# --- 4. MY PROGRESS (Functional Metacognitive Dashboard) ---
def render_metacognitive_dashboard(uid):
    st.header("📈 Research Progress & Calibration")
    st.info("Visualizing your learning journey and metacognitive accuracy.")

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        # Filter for current user
        user_df = df[df['User_ID'].astype(str).str.strip().str.upper() == str(uid).upper()]
        
        if user_df.empty:
            st.warning("No data found. Complete a module to see your progress.")
            return

        # KPI Metrics
        c1, c2 = st.columns(2)
        c1.metric("Modules Started", len(user_df[user_df['Status'] == 'INITIAL']))
        c2.metric("Mastery Achieved", len(user_df[user_df['Status'] == 'POST']))

        # Visualization: Confidence vs Accuracy
        st.subheader("Metacognitive Calibration")
        conf_map = {"Guessing": 25, "Unsure": 50, "Sure": 75, "Very Sure": 100}
        user_df['Conf_Score'] = user_df['Tier_2 (Confidence_Ans)'].map(conf_map)
        user_df['Is_Correct'] = user_df['Diagnostic_Result'].apply(lambda x: 100 if x == "Correct" else 0)
        
        fig = px.line(user_df, x="Timestamp", y="Conf_Score", title="Confidence Trends Over Time")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Progress error: {e}")

def render_dashboard(user):
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.markdown("""
    ### Welcome to the Chemistry AI-X Learning Portal
    * **Goal:** Enhance conceptual clarity through Socratic Dialogue.
    * **Instructions:** Go to 'Learning Modules', answer the diagnostic, and then discuss with Saathi AI.
    ---
    ### आजको लक्ष्य (Today's Goal)
    मोड्युल पूरा गर्नुहोस् र साथी AI सँग छलफल गर्नुहोस्।
    """)
