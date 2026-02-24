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
    choice = st.sidebar.radio("Menu", ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"])

    if choice == "🏠 Dashboard":
        st.title(f"नमस्ते, {user['Name']}! 🙏")
        st.info("Start a module to chat with Saathi AI.")
    
    elif choice == "📚 Learning Modules":
        render_modules(uid, group)
        
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid)
        
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)

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
            
            # REVISION MODE CHECK
            if st.session_state.get(f"mastery_{m_id}"):
                st.warning("🌟 Mastery Detected! Please revise your reasoning.")
                t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reason)", key=f"t5_{idx}")
                t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Revised Confidence)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")
                if st.button("Submit Final Mastery", key=f"fbtn_{idx}"):
                    log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", "MASTERY", get_nepal_time(), t5, t6, "Mastered", "Resolved")
                    st.session_state[f"mastery_{m_id}"] = False
                    st.balloons()
                    st.rerun()
            else:
                st.write(f"Question: {row['Diagnostic_Question']}")
                t1 = st.radio("Answer", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                t2 = st.select_slider("Confidence (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                t3 = st.text_area("Reasoning (Tier 3)", key=f"t3_{idx}")
                t4 = st.select_slider("Reasoning Confidence (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                
                if st.button("Submit Initial Thought", key=f"btn_{idx}"):
                    log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                    st.session_state.current_topic = m_id
                    st.session_state.logic_tree = row['Socratic_Tree']
                    st.success("Log recorded. Go to Saathi AI!")

    except Exception as e: st.error(f"Error: {e}")

def render_ai_chat(uid):
    st.title("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic', 'Science')
    logic = st.session_state.get('logic_tree', 'Scientific inquiry')

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"You are Saathi AI. Help student understand {logic}. If they explain it right, end with: [MASTERY_DETECTED]"}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic to Saathi AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.success("🎯 Saathi AI is satisfied! Go back to Modules to finish.")
        
        st.chat_message("assistant").markdown(ai_reply)
        log_temporal_trace(uid, "CHAT_TURN", f"S: {prompt} | AI: {ai_reply}")
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

def render_metacognitive_dashboard(uid):
    st.title("📈 Progress Analytics")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        data = df[df['User_ID'].astype(str) == str(uid)]
        
        if data.empty: return

        st.subheader("🔄 Confidence Transformation (Sankey)")
        fig = go.Figure(data=[go.Sankey(
            node = dict(pad=15, label=["Pre: Guess", "Pre: Sure", "Post: Unsure", "Post: Mastered"], color="royalblue"),
            link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[2, 8, 5, 1])
        )])
        st.plotly_chart(fig, use_container_width=True)
    except: pass
