import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- HELPERS ---
def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first)")
        st.stop()
        
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(user.get('User_ID'))

# --- 1. DASHBOARD ---
def render_dashboard(user):
    st.title(f"नमस्ते, {user['Name']}! 🙏")
    st.markdown("### साथी (Saathi) AI सिकाई पोर्टलमा स्वागत छ")
    st.info("तपाईंको आजको लक्ष्य: मोड्युल पढ्नुहोस् र साथी AI सँग छलफल गर्नुहोस्।")

# --- 2. MODULES WITH TIER 5-6 REVISION ---
def render_modules(student_group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            m_name = row['Sub_Title']
            st.markdown(f"### 📖 {m_name}")
            
            # Identify if student is in Revision Mode
            is_mastery = st.session_state.get(f"mastery_{m_name}", False)

            if not is_mastery:
                st.write(f"**प्रश्न (Question):** {row['Diagnostic_Question']}")
                ans = st.radio(f"Tier 1: सही उत्तर", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                conf1 = st.select_slider(f"Tier 2 (Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                reason = st.text_area(f"Tier 3 (Reasoning)", key=f"t3_{idx}")
                conf2 = st.select_slider(f"Tier 4 (Reasoning Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

                if st.button("Submit Initial Thoughts", key=f"btn_{idx}"):
                    # Log Initial Assessment
                    log_assessment(st.session_state.user['User_ID'], student_group, m_name, ans, conf1, reason, conf2, "INITIAL", get_nepal_time(), "", "")
                    st.session_state.current_topic = m_name
                    st.session_state.logic_tree = row['Socratic_Tree']
                    st.session_state.last_tier3_reasoning = reason
                    st.success("सफलतापूर्वक बुझाइयो! अब साथी AI सँग छलफल गर्नुहोस्।")
            else:
                st.warning("🌟 परिमार्जन मोड (Revision Mode Active)")
                st.write(f"**अघिल्लो तर्क (Previous Reason):** {st.session_state.get('last_tier3_reasoning', 'N/A')}")
                rev_reason = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{idx}")
                rev_conf = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Revised Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")

                if st.button("Save Final Mastery", key=f"m_btn_{idx}"):
                    # Log Post-Intervention Revision
                    log_assessment(st.session_state.user['User_ID'], student_group, m_name, "REVISED", "N/A", "N/A", "N/A", "MASTERY", get_nepal_time(), rev_reason, rev_conf)
                    st.session_state[f"mastery_{m_name}"] = False
                    st.balloons()
                    st.rerun()
            st.divider()
    except Exception as e:
        st.error(f"Error loading modules: {e}")

# --- 3. SAATHI AI (REFINED MASTERY DETECTION) ---
def render_ai_chat(group_name):
    st.header("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic', 'General Science')
    logic = st.session_state.get('logic_tree', 'Scientific inquiry')

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"You are Saathi AI, a Socratic tutor for Grade 8-10. Help student understand: {logic}."}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("साथी AI लाई सोध्नुहोस्..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        # High-Fidelity Mastery Check
        mastery_check = f"""
        Role: Socratic Tutor. Target Concept: {logic}.
        If the student explains the science correctly, end your message with: [MASTERY_DETECTED]. 
        Be encouraging but do not give the answer!
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": mastery_check}] + st.session_state.messages
        )
        ai_reply = response.choices[0].message.content
        
        if "[MASTERY_DETECTED]" in ai_reply:
            st.session_state[f"mastery_{topic}"] = True
            st.success("🎯 Mastery Reached! Please return to 'Learning Modules' to revise your answer.")
            st.markdown(ai_reply.replace("[MASTERY_DETECTED]", ""))
        else:
            st.markdown(ai_reply)
        
        # Log BOTH student and AI text for researcher portal
        log_temporal_trace(st.session_state.user['User_ID'], "DIALOGUE_TURN", f"Student: {prompt} | AI: {ai_reply}")
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

# --- 4. PROGRESS DASHBOARD (SANKEY & PERSONAS) ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress Dashboard)")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]

        if user_data.empty:
            st.info("No data yet. Complete a module to see your progress.")
            return

        # SANKEY DIAGRAM: Flow from Tier 2 to Tier 6
        st.subheader("🔄 Thinking Transformation")
        st.write("This diagram shows how your confidence changed after talking to Saathi AI.")
        
        
        
        # Static example for research visualization
        fig = go.Figure(data=[go.Sankey(
            node = dict(pad=15, thickness=20, label=["Initial Guess", "Initial Sure", "Final Unsure", "Final Mastery"], color="blue"),
            link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[5, 10, 2, 1])
        )])
        st.plotly_chart(fig, use_container_width=True)

        # PERSONA DISTRIBUTION (Mockup for Researcher Vision)
        st.subheader("🧠 Student Learning Type")
        persona_df = pd.DataFrame({
            "Category": ["Well-Calibrated", "Overconfident", "Lucky Guess", "Struggling"],
            "Count": [4, 1, 2, 1]
        })
        fig_bar = px.bar(persona_df, x="Category", y="Count", color="Category", title="Metacognitive Distribution")
        st.plotly_chart(fig_bar)

    except Exception as e:
        st.error(f"Dashboard Error: {e}")
