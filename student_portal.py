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
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("Please login first!")
        st.stop()
        
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    choice = st.sidebar.radio("Go to", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(user.get('User_ID'))

def render_dashboard(user):
    st.title(f"नमस्ते, {user['Name']}! 🙏")
    st.info("तपाईंको सिकाई यात्राको स्थिति यहाँ हेर्नुहोस्।")

def render_modules(student_group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            m_id = row['Sub_Title']
            st.markdown(f"### 📖 {m_id}")
            
            # Check if student reached mastery in AI chat
            is_mastery = st.session_state.get(f"mastery_{m_id}", False)

            if not is_mastery:
                st.write(f"**प्रश्न:** {row['Diagnostic_Question']}")
                t1 = st.radio(f"Tier 1", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                t2 = st.select_slider(f"Tier 2", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                t3 = st.text_area(f"Tier 3 (Scientific Reason)", key=f"t3_{idx}")
                t4 = st.select_slider(f"Tier 4", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

                if st.button("Submit First Thought", key=f"btn_{idx}"):
                    # Log with placeholders for T5/T6
                    log_assessment(st.session_state.user['User_ID'], student_group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time(), "", "", "Pending", "None")
                    st.session_state.current_topic = m_id
                    st.session_state.logic_tree = row['Socratic_Tree']
                    st.session_state.last_tier3_reasoning = t3
                    st.success("अब साथी (Saathi) AI सँग छलफल गर्नुहोस्!")
            else:
                st.warning("🌟 Post-Intervention Revision Mode Active")
                st.write(f"**तपाईको अघिल्लो तर्क:** {st.session_state.get('last_tier3_reasoning')}")
                t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{idx}")
                t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Revised Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")

                if st.button("Update and Finish Module", key=f"m_btn_{idx}"):
                    log_assessment(st.session_state.user['User_ID'], student_group, m_id, "REVISED", "N/A", "N/A", "N/A", "MASTERY", get_nepal_time(), t5, t6, "Corrected", "Conceptual Shift")
                    st.session_state[f"mastery_{m_id}"] = False
                    st.balloons()
                    st.rerun()
            st.divider()
    except Exception as e: st.error(f"Error: {e}")

def render_ai_chat(group_name):
    st.header("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic', 'General Science')
    logic = st.session_state.get('logic_tree', 'Scientific inquiry')

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"You are Saathi AI. Tutor student on {topic}. Logic: {logic}."}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("साथी AI लाई सोध्नुहोस्..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"If student explains {logic}, end with [MASTERY_DETECTED]"}] + st.session_state.messages
        )
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.success("🎯 Mastery Reached! Return to Modules to revise.")
            st.markdown(ai_reply.replace("[MASTERY_DETECTED]", ""))
        else:
            st.markdown(ai_reply)
        
        log_temporal_trace(st.session_state.user['User_ID'], "DIALOGUE_TURN", f"S: {prompt} | AI: {ai_reply}")
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

def render_metacognitive_dashboard(uid):
    st.title("📈 My Progress Dashboard")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]

        if user_data.empty:
            st.info("No data available.")
            return

        st.subheader("🔄 Knowledge Flow (Sankey Diagram)")
        
        
        # Conceptual Sankey showing confidence shift
        fig = go.Figure(data=[go.Sankey(
            node = dict(pad=15, thickness=20, label=["Guess (Initial)", "Sure (Initial)", "Unsure (Final)", "Mastery (Final)"], color="blue"),
            link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[5, 10, 3, 2])
        )])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🧠 Metacognitive Distributions")
        persona_df = pd.DataFrame({
            "Type": ["Well-Calibrated", "Misconception", "Lucky Guess"],
            "Count": [len(user_data[user_data['Misconception_Tag'] == 'None']), 
                      len(user_data[user_data['Misconception_Tag'] == 'Conceptual Shift']),
                      2]
        })
        st.plotly_chart(px.bar(persona_df, x="Type", y="Count", color="Type"))

    except Exception as e: st.error(f"Dashboard Error: {e}")
