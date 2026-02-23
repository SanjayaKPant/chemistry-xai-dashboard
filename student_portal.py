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
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Group: {student_group}")
    
    if 'current_nav' not in st.session_state:
        st.session_state.current_nav = "🏠 Dashboard"
        
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_nav))
    st.session_state.current_nav = choice

    if choice == "🏠 Dashboard":
        render_dashboard(user, student_group)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user, group):
    st.title("🚀 Student Command Center")
    st.info(f"Current Time (Nepal): {get_nepal_time()}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🎯 **Step 1:** Complete your Module Quiz.")
    with col2:
        st.warning("🤖 **Step 2:** Discuss your reasoning with the AI Tutor.")

def render_modules(student_group):
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Metacognitive Learning Path</h1>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.get('last_submission_success'):
        st.success("✅ Assessment Submitted Successfully!")
        if st.button("🚀 Enter Socratic Chat", use_container_width=True):
            st.session_state.current_nav = "🤖 Socratic Tutor"
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
            
            # Resources
            c1, c2 = st.columns(2)
            with c1: st.link_button("📄 View PDF Notes", row['File_Links (PDF/Images)'], use_container_width=True)
            with c2: st.link_button("Watch Video", row['Video_Links'], use_container_width=True)

            # --- 4 TIERS (STRICT VERTICAL ORDER) ---
            st.write(f"**Question:** {row['Diagnostic_Question']}")
            
            ans = st.radio(f"**Tier 1: Select your answer**", 
                           [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"q{idx}_t1")
            
            conf1 = st.select_slider(f"**Tier 2: How confident are you in this answer?**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t2")
            
            reason = st.text_area(f"**Tier 3: Scientific Reasoning (Required)**", 
                                  placeholder="Explain the chemical principles...", key=f"q{idx}_t3")
            
            conf2 = st.select_slider(f"**Tier 4: How confident are you in your reasoning?**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t4")

            if st.button(f"Submit Assessment", key=f"btn_{idx}", use_container_width=True):
                if not reason.strip() or len(reason.strip()) < 10:
                    st.error("⚠️ Please provide a more detailed scientific reasoning (Tier 3).")
                else:
                    # Log to Google Sheets
                    success = log_assessment(
                        st.session_state.user['User_ID'], 
                        student_group, 
                        row['Sub_Title'], 
                        ans, conf1, reason, conf2, 
                        "Complete", 
                        get_nepal_time()
                    )
                    if success:
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        log_temporal_trace(st.session_state.user['User_ID'], "QUIZ_SUBMIT", row['Sub_Title'])
                        st.rerun()
            st.divider()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_ai_chat(group_name):
    st.subheader("🤖 Socratic Chemistry Tutor")
    
    # Initialize OpenAI Client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # 1. Initialize Chat History if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 2. Display existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Chat Input Space
    if prompt := st.chat_input("Ask your chemistry question..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 4. Generate AI Response (Socratic)
        with st.chat_message("assistant"):
            # Get the Socratic instructions from your session state/Excel
            system_prompt = f"You are a Socratic chemistry tutor. {st.session_state.get('logic_tree', 'Guide the student with questions.')}"
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *st.session_state.messages
                ]
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
            
        # Add AI response to history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
def render_progress(uid):
    st.title("📈 My Learning Progress")
    st.write(f"Showing activity for User: {uid}")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]
        
        if not user_data.empty:
            # Simple chart of confidence over time
            st.dataframe(user_data[['Timestamps', 'Module_ID', 'Tier_2 (Confidence_Ans)', 'Tier_4 (Confidence_Reas)']])
        else:
            st.info("No assessment data recorded yet.")
    except Exception as e:
        st.error(f"Could not load progress: {e}")
