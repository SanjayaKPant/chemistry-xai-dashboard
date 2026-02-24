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
    if 'user' not in st.session_state: st.stop()
    user = st.session_state.user
    uid, group = user.get('User_ID'), str(user.get('Group', 'School A')).strip()

    # Define Tabs for seamless redirection
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    
    # Session state for navigation control
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = menu[0]

    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_tab))
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard":
        st.title(f"नमस्ते, {user['Name']}! 🙏")
        st.info("यो पोर्टल तपाईंको विज्ञान सिकाइमा मद्दत गर्न डिजाइन गरिएको हो।")

    elif choice == "📚 Learning Modules":
        render_modules(uid, group)

    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid)

    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)

# --- 2. THE 6-TIER SOCRATIC LOOP ---
def render_modules(uid, group):
    st.title("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    modules = df[df['Group'] == group]

    for idx, row in modules.iterrows():
        m_id = row['Sub_Title']
        st.subheader(f"📖 {m_id}")

        # CHECK IF PREVIOUS MODULE IS LOCKED (Conceptual Scaffolding)
        # This suspends the module if the student hasn't completed the previous Saathi AI session
        if st.session_state.get("ai_session_active") and st.session_state.get("current_topic") != m_id:
            st.lock("🔒 Please complete your current discussion with Saathi AI first.")
            continue

        # REVISION MODE (Tiers 5 & 6) - Unlocked only after Saathi AI detects mastery
        if st.session_state.get(f"mastery_{m_id}"):
            st.success("🎯 साथी AI: 'तपाईंको बुझाइ अब प्रष्ट भएको छ। कृपया अन्तिम तर्क दिनुहोस्।'")
            t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{idx}")
            t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Post-Intervention Confidence)", 
                                 ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")
            
            if st.button("Submit & Finalize Module", key=f"fbtn_{idx}"):
                log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", "POST", get_nepal_time(), t5, t6, "Corrected", "Resolved")
                st.session_state[f"mastery_{m_id}"] = False
                st.session_state.ai_session_active = False
                st.balloons()
                st.rerun()
        
        else:
            # INITIAL MODE (Tiers 1-4)
            st.write(f"**Diagnostic Question:** {row['Diagnostic_Question']}")
            t1 = st.radio("उत्तर छान्नुहोस् (Tier 1)", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
            t2 = st.select_slider("आत्मविश्वास (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
            t3 = st.text_area("तपाईंको वैज्ञानिक तर्क (Tier 3 Reasoning)", key=f"t3_{idx}")
            t4 = st.select_slider("तर्कमा आत्मविश्वास (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

            if st.button("Submit & Open Saathi AI", key=f"btn_{idx}"):
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                # RESEARCH CONTROL: Lock student into the AI interface
                st.session_state.current_topic = m_id
                st.session_state.logic_tree = row['Socratic_Tree']
                st.session_state.initial_reasoning = t3
                st.session_state.ai_session_active = True
                
                # AUTOMATIC REDIRECTION to Saathi AI Tab
                st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                st.rerun()

# --- 3. SAATHI AI (SOCRATIC CONSTRAINTS) ---
def render_ai_chat(uid):
    st.title("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic')
    
    if not topic:
        st.warning("मोड्युलमा गएर पहिले प्रश्नको उत्तर दिनुहोस्। (Please submit Tier 1-4 first)")
        return

    st.info(f"हामी **{topic}** को बारेमा छलफल गर्दैछौं।")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"""
            You are 'Saathi AI' (साथी AI), a Socratic tutor for high school students in Nepal.
            OBJECTIVE: Use the Socratic method to lead the student to: {st.session_state.logic_tree}.
            CONSTRAINTS:
            1. Language: Use simple English. Understand Nepali and Roman Nepali.
            2. Personality: Helpful, polite, like a companion.
            3. Responses: Short (max 3 sentences).
            4. Socratic: NEVER give the answer. Ask probing questions based on their reasoning: '{st.session_state.initial_reasoning}'.
            5. EXIT: When the student explains the concept correctly, say politely: 
               'तपाईंको बुझाइ प्रष्ट भयो! अब मोड्युलमा गएर आफ्नो उत्तर परिमार्जन गर्नुहोस्। [MASTERY_DETECTED]'
        """}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask Saathi AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(model="gpt-4o-mini", messages=st.session_state.messages)
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.success("🎯 Mastery Detected! Re-directing to Learning Modules for Tiers 5 & 6...")
            
            # Auto-redirection after 2 seconds
            st.session_state.current_tab = "📚 Learning Modules"
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
        
        st.chat_message("assistant").markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        log_temporal_trace(uid, "CHAT", f"S: {prompt} | AI: {ai_reply[:50]}")

# --- 4. PROGRESS ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress)")
    
    # Restored the Sankey visualization for research reporting
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, label=["Guessing", "Sure", "Post-Unsure", "Mastery"], color="royalblue"),
        link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[2, 8, 5, 1])
    )])
    st.plotly_chart(fig, use_container_width=True)
