import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- HELPERS ---
def get_nepal_time():
    """Adjusts UTC (Streamlit Server) to Nepal Time (UTC +5:45)"""
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    """Main entry point called by main_app.py"""
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("Please login first!")
        st.stop()
        
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Group: {student_group}")
    
    if 'current_nav' not in st.session_state:
        st.session_state.current_nav = "🏠 Dashboard"
        
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_nav))
    st.session_state.current_nav = choice

    if choice == "🏠 Dashboard":
        render_dashboard(user, student_group)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user, group):
    st.title("🚀 Student Command Center")
    st.info(f"Current Time (Nepal): {get_nepal_time()}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🎯 **चरण १ (Step 1):** आफ्नो मोड्युल क्विज पूरा गर्नुहोस्। (Complete your Module Quiz.)")
    with col2:
        st.warning("🤖 **चरण २ (Step 2):** साथी AI सँग छलफल गर्नुहोस्। (Discuss with Saathi AI.)")

def render_modules(student_group):
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Metacognitive Learning Path</h1>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.get('last_submission_success'):
        st.success("✅ Assessment Submitted Successfully!")
        if st.button("🚀 साथी AI सँग कुरा गर्नुहोस् (Chat with Saathi AI)", use_container_width=True):
            st.session_state.current_nav = "🤖 साथी (Saathi) AI"
            st.session_state.last_submission_success = False
            st.rerun()
        return 

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            st.markdown(f"### 📖 {row['Sub_Title']}")
            
            c1, c2 = st.columns(2)
            with c1: st.link_button("📄 View PDF Notes", row['File_Links (PDF/Images)'], use_container_width=True)
            with c2: st.link_button("Watch Video", row['Video_Links'], use_container_width=True)

            st.write(f"**Question:** {row['Diagnostic_Question']}")
            
            # --- BILINGUAL 4-TIER ASSESSMENT ---
            ans = st.radio(f"**Tier 1: सही उत्तर छान्नुहोस् (Select answer)**", 
                           [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"q{idx}_t1")
            
            conf1 = st.select_slider(f"**Tier 2: तपाईं यो उत्तरमा कत्तिको विश्वस्त हुनुहुन्छ? (Confidence)**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t2")
            
            reason = st.text_area(f"**Tier 3: वैज्ञानिक तर्क (Scientific Reasoning - Required)**", 
                                  placeholder="यसको पछाडिको वैज्ञानिक कारण लेख्नुहोस्...", key=f"q{idx}_t3")
            
            conf2 = st.select_slider(f"**Tier 4: तपाईं आफ्नो तर्कमा कत्तिको विश्वस्त हुनुहुन्छ? (Reasoning Confidence)**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t4")

            if st.button(f"Submit Assessment", key=f"btn_{idx}", use_container_width=True):
                if not reason.strip() or len(reason.strip()) < 10:
                    st.error("⚠️ कृपया थप विस्तृत वैज्ञानिक तर्क दिनुहोस्। (Provide more reasoning).")
                else:
                    success = log_assessment(
                        st.session_state.user['User_ID'], 
                        student_group, 
                        row['Sub_Title'], 
                        ans, conf1, reason, conf2, 
                        "Complete", 
                        get_nepal_time()
                    )
                    if success:
                        # Store context for Saathi AI
                        st.session_state.last_question_text = row['Diagnostic_Question']
                        st.session_state.last_mcq_choice = ans
                        st.session_state.last_tier3_reasoning = reason
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        log_temporal_trace(st.session_state.user['User_ID'], "QUIZ_SUBMIT", row['Sub_Title'])
                        st.rerun()
            st.divider()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_ai_chat(group_name):
    st.markdown("<h2 style='color: #1E3A8A;'>🤖 साथी (Saathi) AI</h2>", unsafe_allow_html=True)
    st.caption("तपाईंको विज्ञान साथी - Your Socratic Science Companion (Grades 8-10)")

    # Retrieve context from the last assessment
    last_q = st.session_state.get('last_question_text', 'a science concept')
    last_ans = st.session_state.get('last_mcq_choice', 'None')
    last_reason = st.session_state.get('last_tier3_reasoning', 'Not provided yet')

    with st.expander("⚖️ रिसर्च र नैतिक खुलासा (Research & Ethical Disclosure)"):
        st.write("Saathi AI helps you think, it doesn't just give answers. Your data is used for PhD research.")

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Context-Aware Priming
        st.session_state.messages.append({
            "role": "system", 
            "content": f"Student answered: '{last_q}'. Selected: '{last_ans}'. Reason: '{last_reason}'."
        })

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("तपाईंको जिज्ञासा यहाँ लेख्नुहोस् (Write here)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            system_prompt = f"""
            You are 'Saathi AI' (साथी AI), a Socratic tutor for Grade 8-10 students in Nepal.
            CONTEXT: Question: {last_q} | Choice: {last_ans} | Reasoning: {last_reason}
            RULES:
            1. NEVER give the answer.
            2. Probe the student's reasoning ({last_reason}).
            3. Use simple English and encouraging Nepali phrases like 'राम्रो प्रयास!'.
            4. Keep responses under 3 sentences.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
            )
            ai_reply = response.choices[0].message.content
            st.markdown(ai_reply)
            
            log_temporal_trace(st.session_state.user['User_ID'], "AI_CHAT", f"AI: {ai_reply[:50]}")
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})

def render_progress(uid):
    st.title("📈 My Learning Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]
        if not user_data.empty:
            st.dataframe(user_data[['Timestamps', 'Module_ID', 'Tier_2 (Confidence_Ans)', 'Tier_4 (Confidence_Reas)']])
    except Exception as e:
        st.error(f"Error: {e}")
