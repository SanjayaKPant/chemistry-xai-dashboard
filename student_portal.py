import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state: st.stop()
    user = st.session_state.user
    uid, group = user.get('User_ID'), str(user.get('Group')).strip()

    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "📚 Learning Modules":
        render_modules(uid, group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)
    else:
        st.title(f"नमस्ते, {user['Name']}! 🙏")
        st.info("मोड्युल सुरु गर्न 'Learning Modules' मा जानुहोस्।")

def render_modules(uid, group):
    st.title("📚 Learning Modules")
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    modules = df[df['Group'] == group]

    for idx, row in modules.iterrows():
        m_id = row['Sub_Title']
        st.subheader(f"📖 {m_id}")
        
        # Mastery Check: If AI marked this topic as mastered
        if st.session_state.get(f"mastery_{m_id}"):
            st.success("🌟 Conceptual Shift Detected! Please provide your final scientific reasoning.")
            t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{idx}")
            t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Final Confidence)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")
            if st.button("Complete Module", key=f"fbtn_{idx}"):
                log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", "MASTERY", get_nepal_time(), t5, t6, "Corrected", "Resolved")
                st.session_state[f"mastery_{m_id}"] = False
                st.balloons()
                st.rerun()
        else:
            st.write(f"**Question:** {row['Diagnostic_Question']}")
            t1 = st.radio("Choose Answer", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
            t2 = st.select_slider("Confidence (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
            t3 = st.text_area("Reasoning (Tier 3)", key=f"t3_{idx}", placeholder="Why do you think this is the answer?")
            t4 = st.select_slider("Reasoning Confidence (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
            
            if st.button("Submit & Start AI Discussion", key=f"btn_{idx}"):
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                # STORE SUBMISSION FOR AI CONTEXT
                st.session_state.current_topic = m_id
                st.session_state.submitted_ans = t1
                st.session_state.submitted_reason = t3
                st.session_state.logic_tree = row['Socratic_Tree']
                st.success("Submission recorded! Now open 'Saathi AI' to discuss.")

def render_ai_chat(uid):
    st.title("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic')
    
    if not topic:
        st.warning("Please submit a module first!")
        return

    # AI context injection: Telling the AI what the student chose
    ans = st.session_state.get('submitted_ans')
    reason = st.session_state.get('submitted_reason')
    logic = st.session_state.get('logic_tree')

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"""
            You are Saathi AI, a Socratic Tutor. 
            STUDENT SUBMISSION:
            - Topic: {topic}
            - Their Choice: {ans}
            - Their Reasoning: {reason}
            - Scientific Goal: {logic}
            
            TASK: Probe the student's reasoning. Do not give the answer. 
            If they explain the concept correctly, say exactly: [MASTERY_DETECTED].
        """}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Talk to Saathi AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.success("🎯 Saathi AI has confirmed your understanding! Go to Modules to finalize.")
        
        st.chat_message("assistant").markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        log_temporal_trace(uid, "CHAT", f"S: {prompt} | AI: {ai_reply[:50]}")

def render_metacognitive_dashboard(uid):
    st.title("📈 Metacognitive Progress")
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, label=["Initial Guess", "Initial Sure", "Final Mastery"]),
        link = dict(source=[0, 1], target=[2, 2], value=[5, 10])
    )])
    st.plotly_chart(fig)
