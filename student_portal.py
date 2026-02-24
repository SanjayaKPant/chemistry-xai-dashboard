import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- HELPERS ---
def get_nepal_time():
    """Adjusts UTC to Nepal Time (UTC +5:45)"""
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    """Main entry point called by main_app.py"""
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first)")
        st.stop()
        
    user = st.session_state.user
    uid = user.get('User_ID')
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {student_group}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    choice = st.sidebar.radio("तपाईं कहाँ जान चाहनुहुन्छ?", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(uid, student_group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid, student_group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)

# --- 1. DASHBOARD ---
def render_dashboard(user):
    st.title(f"नमस्ते, {user['Name']}! 🙏")
    st.markdown("### साथी (Saathi) AI सिकाई पोर्टलमा स्वागत छ")
    st.info("तपाईंको आजको लक्ष्य: मोड्युल पढ्नुहोस् र साथी AI सँग छलफल गर्नुहोस्।")
    
    # Quick Stats for Student
    st.subheader("Your Journey Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Modules Started", "3")
    col2.metric("Mastery Reached", "1")
    col3.metric("AI Chats", "12")

# --- 2. MODULES WITH 6-TIER LOGIC ---
def render_modules(uid, student_group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        if modules.empty:
            st.warning("No modules assigned to your group yet.")
            return

        for idx, row in modules.iterrows():
            m_id = row['Sub_Title']
            st.markdown(f"## 📖 {m_id}")
            
            # Revision Mode Toggle: Only active if Saathi AI detected mastery
            is_mastery = st.session_state.get(f"mastery_{m_id}", False)

            if not is_mastery:
                # TIERS 1-4: INITIAL ASSESSMENT
                st.write(f"**प्रश्न (Diagnostic Question):** {row['Diagnostic_Question']}")
                
                options = [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']]
                t1 = st.radio(f"Tier 1: सही उत्तर छान्नुहोस्", options, key=f"t1_{idx}")
                
                conf_options = ["Guessing", "Unsure", "Sure", "Very Sure"]
                t2 = st.select_slider(f"Tier 2: तपाईं कत्तिको विश्वस्त हुनुहुन्छ?", options=conf_options, key=f"t2_{idx}")
                
                t3 = st.text_area(f"Tier 3: तपाईंको वैज्ञानिक तर्क दिनुहोस् (Scientific Reasoning)", key=f"t3_{idx}")
                
                t4 = st.select_slider(f"Tier 4: तपाईंको तर्कमा कत्तिको विश्वस्त हुनुहुन्छ?", options=conf_options, key=f"t4_{idx}")

                if st.button("Submit Initial Thoughts", key=f"btn_{idx}"):
                    # Log to 12-column Sheet (T5 and T6 are empty for now)
                    success = log_assessment(
                        uid, student_group, m_id, t1, t2, t3, t4, 
                        "INITIAL", get_nepal_time(), "", "", "Pending", "None"
                    )
                    if success:
                        st.session_state.current_topic = m_id
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_tier3_reasoning = t3
                        st.success("सफलतापूर्वक बुझाइयो! अब साथी AI सँग छलफल गरेर आफ्नो धारणा प्रष्ट पार्नुहोस्।")
            
            else:
                # TIERS 5-6: POST-INTERVENTION MASTERY
                st.warning("🎯 साथी (Saathi) AI ले तपाईंको बुझाइ राम्रो भएको महसुस गरेको छ!")
                st.write(f"**तपाईको अघिल्लो तर्क:** _{st.session_state.get('last_tier3_reasoning', '')}_")
                
                t5 = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Scientific Reasoning)", key=f"t5_{idx}")
                t6 = st.select_slider("Tier 6: नयाँ आत्मविश्वास (New Confidence Level)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")

                if st.button("Finalize and Save Mastery", key=f"m_btn_{idx}"):
                    # Log Final Mastery
                    log_assessment(
                        uid, student_group, m_id, "REVISED", "N/A", "N/A", "N/A", 
                        "MASTERY", get_nepal_time(), t5, t6, "Corrected", "Resolved"
                    )
                    st.session_state[f"mastery_{m_id}"] = False # Reset flag after saving
                    st.balloons()
                    st.success("बधाई छ! तपाईंले यो मोड्युल पूरा गर्नुभयो।")
                    st.rerun()
            st.divider()
    except Exception as e:
        st.error(f"Error loading modules: {e}")

# --- 3. SAATHI AI CHAT ---
def render_ai_chat(uid, group_name):
    st.title("🤖 साथी (Saathi) AI")
    
    topic = st.session_state.get('current_topic')
    if not topic:
        st.warning("कृपया पहिले 'Learning Modules' मा गएर कुनै एउटा विषय छान्नुहोस्।")
        return

    st.subheader(f"Topic: {topic}")
    logic = st.session_state.get('logic_tree', 'General Science inquiry')

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": f"""You are 'Saathi AI' (साथी AI), a Socratic tutor for students in Nepal.
            OBJECTIVE: Guide the student to understand: {logic}.
            RULES: 
            1. NEVER give the direct answer. 
            2. If the student provides a correct scientific explanation, you MUST end your response with the exact phrase: [MASTERY_DETECTED].
            3. Use simple English and occasional Nepali encouragement like 'राम्रो प्रयास!'.
            """}
        ]

    # Display Chat History
    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    if prompt := st.chat_input("साथी AI सँग कुरा गर्नुहोस्..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Call OpenAI
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages
            )
            ai_reply = response.choices[0].message.content
            
            # Check for Mastery Detection
            if "[MASTERY_DETECTED]" in ai_reply:
                st.session_state[f"mastery_{topic}"] = True
                clean_reply = ai_reply.replace("[MASTERY_DETECTED]", "")
                with st.chat_message("assistant"):
                    st.markdown(clean_reply)
                    st.success("🎯 Mastery Detection: You have explained the concept correctly! Go to 'Learning Modules' to finalize your answer.")
                st.session_state.messages.append({"role": "assistant", "content": clean_reply})
            else:
                with st.chat_message("assistant"):
                    st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            
            # Log Temporal Trace for PhD Qualitative Analysis
            log_temporal_trace(uid, "CHAT_TURN", f"Student: {prompt} | AI: {ai_reply}")

        except Exception as e:
            st.error(f"AI Connection Error: {e}")

# --- 4. METACOGNITIVE PROGRESS DASHBOARD ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress Dashboard)")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]

        if user_data.empty:
            st.info("अझै कुनै डाटा छैन। मोड्युल पूरा गरेपछि यहाँ प्रगति देखिनेछ।")
            return

        # SANKEY DIAGRAM: Visualizing Confidence Shift
        st.subheader("🔄 Thinking Transformation")
        st.write("यो रेखाचित्रले साथी AI सँगको कुराकानी पछि तपाईंको आत्मविश्वासमा आएको परिवर्तन देखाउँछ।")
        
        # We simulate the flow from Tier 2 (Initial) to Tier 6 (Final)
        fig = go.Figure(data=[go.Sankey(
            node = dict(
              pad = 15,
              thickness = 20,
              line = dict(color = "black", width = 0.5),
              label = ["Initial: Unsure", "Initial: Sure", "Final: Unsure", "Final: Mastery"],
              color = ["#E6B0AA", "#A9CCE3", "#F9E79F", "#ABEBC6"]
            ),
            link = dict(
              source = [0, 1, 0, 1], 
              target = [2, 3, 3, 2],
              value = [2, 8, 5, 1] # Sample values for visualization
          ))])
        st.plotly_chart(fig, use_container_width=True)

        # LEARNING PERSONA
        st.subheader("🧠 Metacognitive Calibration")
        persona_df = pd.DataFrame({
            "Type": ["Well-Calibrated", "Overconfident", "Lucky Guess", "Misconception"],
            "Score": [70, 10, 5, 15]
        })
        fig_bar = px.bar(persona_df, x="Type", y="Score", color="Type", title="Student Learning Profile")
        st.plotly_chart(fig_bar)

    except Exception as e:
        st.error(f"Dashboard Error: {e}")
