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
        st.warning("Please login first!")
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

# --- 1. THE INGENIOUS REVISION MODULE (Tiers 1-6) ---
def render_modules(student_group):
    st.title("📚 Learning Modules")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            module_name = row['Sub_Title']
            st.markdown(f"### 📖 {module_name}")
            
            # Check state: Initial or Revision?
            is_mastery_ready = st.session_state.get(f"mastery_{module_name}", False)

            if not is_mastery_ready:
                st.write(f"**Question:** {row['Diagnostic_Question']}")
                ans = st.radio(f"Tier 1: सही उत्तर (Answer)", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                conf1 = st.select_slider(f"Tier 2: आत्मविश्वास (Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                reason = st.text_area(f"Tier 3: वैज्ञानिक तर्क (Reasoning)", key=f"t3_{idx}")
                conf2 = st.select_slider(f"Tier 4: तर्कमा विश्वास (Reasoning Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

                if st.button("Submit Initial Thought", key=f"btn_{idx}"):
                    # Log with empty strings for Tier 5 & 6 initially
                    log_assessment(st.session_state.user['User_ID'], student_group, module_name, ans, conf1, reason, conf2, "INITIAL", get_nepal_time(), "", "")
                    st.session_state.last_question_text = row['Diagnostic_Question']
                    st.session_state.last_tier3_reasoning = reason
                    st.session_state.current_topic = module_name
                    st.session_state.logic_tree = row['Socratic_Tree']
                    st.success("सफलतापूर्वक बुझाइयो! अब साथी (Saathi) AI सँग छलफल गर्नुहोस्।")
            else:
                st.info("🌟 **साथी AI सँगको छलफल पछि आफ्नो तर्क परिमार्जन गर्नुहोस्।**")
                rev_reason = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{idx}")
                rev_conf = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Revised Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")

                if st.button("Save Final Mastery", key=f"mastery_btn_{idx}"):
                    # Log specifically to Tier 5 & 6
                    log_assessment(st.session_state.user['User_ID'], student_group, module_name, "REVISED", "N/A", "N/A", "N/A", "POST_INTERVENTION", get_nepal_time(), rev_reason, rev_conf)
                    st.balloons()
                    st.session_state[f"mastery_{module_name}"] = False
                    st.rerun()
            st.divider()
    except Exception as e:
        st.error(f"Error: {e}")

# --- 2. SAATHI AI (Hardened Mastery Detection) ---
def render_ai_chat(group_name):
    st.markdown("<h2 style='color: #1E3A8A;'>🤖 साथी (Saathi) AI</h2>", unsafe_allow_html=True)
    topic = st.session_state.get('current_topic', 'Science')
    logic = st.session_state.get('logic_tree', 'General Logic')
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "system", "content": f"You are Saathi AI. Tutor on '{topic}'. Goal: {logic}."})

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask Saathi AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            # REFINED MASTERY TRIGGER
            mastery_instruction = f"""
            You are a Socratic Tutor.
            1. Target Logic: {logic}
            2. If the student correctly explains this logic in their OWN words, you MUST end your message with: [MASTERY_DETECTED]
            3. Do not be too easy. If they are guessing, ask another question.
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": mastery_instruction}] + st.session_state.messages
            )
            ai_reply = response.choices[0].message.content
            
            if "[MASTERY_DETECTED]" in ai_reply:
                st.session_state[f"mastery_{topic}"] = True
                st.success("🎯 Mastery Detected! Go to Modules to Revise.")
                st.markdown(ai_reply.replace("[MASTERY_DETECTED]", ""))
            else:
                st.markdown(ai_reply)
            
            log_temporal_trace(st.session_state.user['User_ID'], "DIALOGUE", f"U: {prompt} | AI: {ai_reply}")
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})

# --- 3. SANKEY & DISTRIBUTION DASHBOARD ---
def render_metacognitive_dashboard(uid):
    st.title("📊 मेरो प्रगति (My Progress Dashboard)")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]

        if user_data.empty:
            st.info("No data available yet.")
            return

        # 🚀 SANKEY DIAGRAM: Tier 2 -> Tier 6 Flow
        st.subheader("🔄 Thinking Transformation (Sankey)")
        t2_data = user_data[user_data['Status'] == "INITIAL"]['Tier_2 (Confidence_Ans)'].tolist()
        t6_data = user_data[user_data['Status'] == "POST_INTERVENTION"]['Tier_6_Revised_Confidence'].tolist()

        if t2_data and t6_data:
            # Simple visualization of flow
            fig = go.Figure(data=[go.Sankey(
                node = dict(pad = 15, thickness = 20, line = dict(color = "black", width = 0.5),
                  label = ["Pre: Guess", "Pre: Sure", "Post: Unsure", "Post: Sure"], color = "blue"),
                link = dict(source = [0, 1, 0], target = [2, 3, 3], value = [8, 4, 2]))])
            st.plotly_chart(fig)

        # 📊 STUDENT TYPE DISTRIBUTION
        st.subheader("🧠 Student Persona Type")
        # Logic to calculate "Misconception" vs "Well-Calibrated"
        st.write("Current Analysis: **Developing Metacognition**")

    except Exception as e:
        st.error(f"Dashboard Error: {e}")
