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

    # Persistent navigation state
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

# --- 2. DASHBOARD ---
def render_dashboard(user):
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.markdown(f"""
    ### Welcome to the Chemistry AI-X Research Portal
    **Today's Goal:** Complete your assigned module and discuss concepts with Saathi AI.
    
    ---
    ### आजको लक्ष्य (Today's Goal)
    मोड्युल पूरा गर्नुहोस् र साथी AI सँग छलफल गर्नुहोस्।
    """)
    st.info("Navigate to **Learning Modules** on the left to begin.")

# --- 3. MODULE ENGINE (Tiers 1-4 Logging) ---
def render_modules(uid, group):
    st.header("Learning Modules | सिकाई मोड्युलहरू")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Check for completed modules (Status = POST)
        all_logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        finished = []
        if not all_logs.empty:
            all_logs['User_ID'] = all_logs['User_ID'].astype(str).str.strip().str.upper()
            finished = all_logs[(all_logs['User_ID'] == uid) & (all_logs['Status'] == 'POST')]['Module_ID'].tolist()

        # Fetch materials for the student's group
        m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        available = m_df[m_df['Group'].astype(str).str.strip() == group]
        
        # Identify the first unfinished module
        active_module = next((row for _, row in available.iterrows() if row['Sub_Title'] not in finished), None)

        if active_module is None:
            st.success("🎉 All modules completed! | सबै मोड्युलहरू पूरा भए!")
            return

        m_id = active_module['Sub_Title']
        st.subheader(f"📖 Concept: {m_id}")

        # The 4-Tier Diagnostic Form
        with st.form("diagnostic_form"):
            st.markdown(f"**Diagnostic Question:** {active_module['Diagnostic_Question']}")
            
            t1 = st.radio("Select Answer:", [
                active_module['Option_A'], 
                active_module['Option_B'], 
                active_module['Option_C'], 
                active_module['Option_D']
            ])
            
            t2 = st.select_slider("Confidence (Tier 2):", ["Guessing", "Unsure", "Sure", "Very Sure"])
            t3 = st.text_area("Reasoning/Explanation (Tier 3):")
            t4 = st.select_slider("Reasoning Confidence (Tier 4):", ["Guessing", "Unsure", "Sure", "Very Sure"])

            if st.form_submit_button("Submit & Start AI Discussion"):
                # Store for AI context
                st.session_state.current_topic = m_id
                st.session_state.active_module_data = active_module
                
                # Log Initial state to Sheets
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                
                # Clear previous chat for new topic
                if "messages" in st.session_state: del st.session_state.messages
                
                st.session_state.current_tab = "🤖 Saathi AI"
                st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

# --- 4. SAATHI AI (Socratic Logic) ---
def render_ai_chat(uid, group):
    topic = st.session_state.get('current_topic')
    module_data = st.session_state.get('active_module_data')

    if not topic or module_data is None:
        st.warning("Please complete a Diagnostic Module first | कृपया पहिले मोड्युल पूरा गर्नुहोस्।")
        return

    st.subheader(f"🤖 Discussion: {topic}")
    
    # Side-by-side: Reference and Chat
    col_ref, col_chat = st.columns([1, 2])
    
    with col_ref:
        st.markdown("### 📍 Reference Material")
        st.write(f"**Question:** {module_data.get('Diagnostic_Question')}")
        link = module_data.get('File_Link')
        if pd.notna(link) and str(link).startswith("http"):
            st.link_button("📄 Open Learning Material", str(link))

    with col_chat:
        # Initialize Chat Messages
        if "messages" not in st.session_state:
            socratic_instructions = module_data.get('Socratic_Tree', 'Guide the student using Socratic questioning.')
            st.session_state.messages = [{"role": "system", "content": f"""
                You are Saathi, a Socratic Chemistry Tutor. 
                STRICT GUIDELINES:
                1. Never give the direct answer.
                2. Use the provided logic: {socratic_instructions}
                3. Support both English and Nepali.
                4. When the student demonstrates full understanding, say: 'बधाई छ! [MASTERY_DETECTED]'
            """}]

        # Display history
        for m in st.session_state.messages:
            if m["role"] != "system":
                with st.chat_message(m["role"]): st.markdown(m["content"])

        # Chat Input
        if prompt := st.chat_input("Ask Saathi AI..."):
            with st.chat_message("user"): st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
                ai_reply = response.choices[0].message.content
                
                # Trace log for research analysis
                log_temporal_trace(uid, f"CHAT_{topic}", f"Prompt: {prompt} | Reply: {ai_reply}")

                if "[MASTERY_DETECTED]" in ai_reply:
                    st.success("Mastery Detected! Updating progress...")
                    # Log final status (Tier 5/6 Mastery)
                    log_assessment(uid, group, topic, "N/A", "Very Sure", "Mastery via AI", "Very Sure", "POST", get_nepal_time())
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.balloons()
                    st.session_state.current_tab = "📚 Learning Modules"
                    st.rerun()

                with st.chat_message("assistant"): st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})

            except Exception as e:
                st.error(f"AI Connection Error: {e}")

# --- 5. MY PROGRESS (Functional Dashboard) ---
def render_metacognitive_dashboard(uid):
    st.header("📈 My Learning Progress | मेरो प्रगति")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        # Clean and Filter
        user_df = df[df['User_ID'].astype(str).str.strip().str.upper() == str(uid).upper()]
        
        if user_df.empty:
            st.info("No research data found yet. Complete a module to see your stats.")
            return

        # Metrics
        m_started = len(user_df[user_df['Status'] == 'INITIAL'])
        m_mastered = len(user_df[user_df['Status'] == 'POST'])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Modules Started", m_started)
        c2.metric("Mastery Achieved", m_mastered)
        c3.metric("Completion Rate", f"{(m_mastered/m_started*100 if m_started > 0 else 0):.0f}%")

        # Visualization: Confidence vs. Time
        st.subheader("Metacognitive Confidence Trend")
        conf_map = {"Guessing": 25, "Unsure": 50, "Sure": 75, "Very Sure": 100}
        user_df['Conf_Score'] = user_df['Tier_2 (Confidence_Ans)'].map(conf_map)
        
        fig = px.line(user_df, x="Timestamp", y="Conf_Score", markers=True, 
                     title="How your confidence has evolved",
                     labels={"Conf_Score": "Confidence Level (%)"})
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning("Progress dashboard is currently syncing with the database.")
