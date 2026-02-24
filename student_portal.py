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
    st.markdown("### साथी (Saathi) AI सिकाई पोर्टलमा स्वागत छ")
    st.info("तपाईंको सिकाई यात्रा यहाँबाट सुरु हुन्छ। 'Learning Modules' मा जानुहोस्।")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Status", "Active Learner")
    with col2:
        st.metric("Research Group", user.get('Group'))

# --- 3. MODULES (THE 6-TIER JOURNEY) ---
def render_modules(uid, group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == group]

        if modules.empty:
            st.warning("तपाईंको समूहको लागि कुनै मोड्युलहरू भेटिएनन्।")
            return

        for idx, row in modules.iterrows():
            m_id = row['Sub_Title']
            st.subheader(f"📖 {m_id}")

            # PhD SCAFFOLDING: Suspend other modules if one is in progress
            if st.session_state.get("ai_session_active") and st.session_state.get("current_topic") != m_id:
                st.warning(f"🔒 पहिले '{st.session_state.get('current_topic')}' को छलफल पूरा गर्नुहोस्।")
                continue

            # TIER 5 & 6: REVISION MODE (Unlocked by AI)
            if st.session_state.get(f"mastery_{m_id}"):
                st.success("🎯 साथी AI ले तपाईंको बुझाइमा सुधार भएको पुष्टि गरेको छ!")
                with st.expander("Finalize your Answer", expanded=True):
                    t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{idx}")
                    t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Final Confidence Level)", 
                                         ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")
                    
                    if st.button("Finalize and Save Mastery", key=f"m_btn_{idx}"):
                        log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", 
                                      "POST", get_nepal_time(), t5, t6, "Corrected", "Resolved")
                        st.session_state[f"mastery_{m_id}"] = False
                        st.session_state.ai_session_active = False
                        st.balloons()
                        st.success("बधाई छ! तपाईंले यो मोड्युल सफलतापूर्वक पूरा गर्नुभयो।")
                        st.rerun()
            
            # TIER 1 - 4: INITIAL DIAGNOSTIC
            else:
                with st.expander("Diagnostic Questions", expanded=not st.session_state.get("ai_session_active")):
                    st.write(f"**प्रश्न:** {row['Diagnostic_Question']}")
                    opts = [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']]
                    t1 = st.radio("सही उत्तर छान्नुहोस् (Tier 1)", opts, key=f"t1_{idx}")
                    t2 = st.select_slider("तपाईं कत्तिको विश्वस्त हुनुहुन्छ? (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                    t3 = st.text_area("वैज्ञानिक तर्क दिनुहोस् (Tier 3 Reasoning)", key=f"t3_{idx}")
                    t4 = st.select_slider("तपाईंको तर्कमा कत्तिको विश्वस्त हुनुहुन्छ? (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

                    if st.button("Submit & Chat with Saathi AI", key=f"btn_{idx}"):
                        log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                        # Store session context
                        st.session_state.current_topic = m_id
                        st.session_state.initial_ans = t1
                        st.session_state.initial_reasoning = t3
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.ai_session_active = True
                        
                        # REDIRECT TO AI
                        st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                        st.rerun()
            st.divider()
    except Exception as e:
        st.error(f"Error: {e}")

# --- 4. SAATHI AI (THE INTERVENTION) ---
def render_ai_chat(uid, group):
    st.title("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic')
    
    if not topic:
        st.warning("पहिले मोड्युलमा गएर उत्तर दिनुहोस्।")
        return

    st.subheader(f"Topic: {topic}")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"""
            You are 'Saathi AI', a polite Socratic tutor for high school students in Nepal.
            OBJECTIVE: Guide the student to understand: {st.session_state.get('logic_tree')}.
            STUDENT CONTEXT: They answered '{st.session_state.get('initial_ans')}' because: '{st.session_state.get('initial_reasoning')}'.
            CONSTRAINTS:
            - Use simple English and support Nepali/Roman Nepali.
            - Short sentences only.
            - NEVER give the answer. Propose analogies.
            - When the concept is clear, end with: 'तपाईंको बुझाइ प्रष्ट भयो! अब मोड्युलमा गएर उत्तर परिमार्जन गर्नुहोस्। [MASTERY_DETECTED]'
        """}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask Saathi AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.success("🎯 Mastery Reached! Redirecting to Learning Modules...")
            st.session_state.current_tab = "📚 Learning Modules"
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
        
        with st.chat_message("assistant"): st.markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        log_temporal_trace(uid, "CHAT_TURN", f"S: {prompt} | AI: {ai_reply[:50]}")

# --- 5. PROGRESS (PhD ANALYTICS) ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress)")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        data = df[df['User_ID'].astype(str) == str(uid)]
        
        if data.empty:
            st.info("अझै कुनै डाटा उपलब्ध छैन।")
            return

        # Visualizing Metacognitive Shifts
        fig = go.Figure(data=[go.Sankey(
            node = dict(pad=15, thickness=20, label=["Guessing (Pre)", "Sure (Pre)", "Unsure (Post)", "Mastery (Post)"], color="#2E86C1"),
            link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[2, 5, 3, 1])
        )])
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Learning History")
        st.dataframe(data[['Timestamps', 'Module_ID', 'Status', 'Tier_2 (Confidence_Ans)']])
    except:
        st.error("Error loading progress.")
