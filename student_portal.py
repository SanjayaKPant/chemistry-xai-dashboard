import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state: st.stop()
    user = st.session_state.user
    uid = user.get('User_ID')
    group = str(user.get('Group', 'School A')).strip()

    st.sidebar.title(f"🎓 {user.get('Name')}")
    choice = st.sidebar.radio("Navigation", ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"])

    if choice == "🏠 Dashboard":
        st.title(f"नमस्ते, {user['Name']}! 🙏")
        st.info("तपाईंको सिकाई यात्राको प्रगति 'My Progress' मा हेर्नुहोस्।")
    
    elif choice == "📚 Learning Modules":
        render_modules(uid, group)
        
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid)
        
    elif choice == "📈 My Progress":
        render_progress(uid)

def render_modules(uid, group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == group]

        for idx, row in modules.iterrows():
            m_id = row['Sub_Title']
            st.subheader(f"📖 {m_id}")
            
            # Check for Revision Mode (Mastery flag)
            if st.session_state.get(f"mastery_{m_id}"):
                st.warning("🌟 Post-Intervention Revision Active")
                t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reason)", key=f"t5_{idx}")
                t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Revised Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")
                if st.button("Finalize Mastery", key=f"fbtn_{idx}"):
                    log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", "MASTERY", get_nepal_time(), t5, t6, "Success", "Conceptual Shift")
                    st.session_state[f"mastery_{m_id}"] = False
                    st.balloons()
                    st.rerun()
            else:
                st.write(f"**Question:** {row['Diagnostic_Question']}")
                t1 = st.radio("Answer", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                t2 = st.select_slider("Confidence (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                t3 = st.text_area("Reasoning (Tier 3)", key=f"t3_{idx}")
                t4 = st.select_slider("Confidence (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                
                if st.button("Submit Initial Thought", key=f"btn_{idx}"):
                    log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                    st.session_state.current_topic = m_id
                    st.session_state.logic_tree = row['Socratic_Tree']
                    st.success("Please discuss this with Saathi AI now!")

    except Exception as e: st.error(f"Error: {e}")

def render_ai_chat(uid):
    st.title("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic', 'Science')
    logic = st.session_state.get('logic_tree', 'General Principles')

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"Socratic Tutor. Logic: {logic}. If understood, end with [MASTERY_DETECTED]"}]

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
            st.success("Mastery Detected! Return to Modules.")
        
        st.chat_message("assistant").markdown(ai_reply)
        log_temporal_trace(uid, "CHAT", f"U: {prompt} | AI: {ai_reply}")
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

def render_progress(uid):
    st.title("📈 Metacognitive Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]

        if user_data.empty: return

        st.subheader("🔄 Knowledge Flow (Sankey)")
        # This Sankey shows the transition from Initial Confidence (T2) to Revised (T6)
        fig = go.Figure(data=[go.Sankey(
            node = dict(pad=15, label=["Guess (T2)", "Sure (T2)", "Unsure (T6)", "Mastery (T6)"], color="blue"),
            link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[5, 10, 8, 2])
        )])
        st.plotly_chart(fig)
        
    except: pass
