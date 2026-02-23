import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from google.generativeai.types import RequestOptions

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {student_group}")
    
    # Dynamic Menu Labels
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    
    # Handle programmatic navigation
    if 'current_nav' not in st.session_state:
        st.session_state.current_nav = "🏠 Dashboard"
        
    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_nav))

    if choice == "🏠 Dashboard":
        render_dashboard(user, student_group)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user, group):
    st.title(f"🚀 Student Command Center")
    st.markdown(f"### Welcome back, {user.get('Name')}!")
    st.info(f"You are currently assigned to the **{group}** research cohort.")
    
    # Quick Summary Cards
    col1, col2 = st.columns(2)
    with col1:
        st.success("🎯 **Goal:** Complete your assigned diagnostic modules.")
    with col2:
        st.warning("🤖 **AI Tutor:** Use the tutor to explain your logic and earn 'Mastery' status.")

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    
    # --- STEP 1: Workflow Handling (If just submitted) ---
    if st.session_state.get('last_submission_success'):
        st.balloons()
        st.markdown("""
            <div style="background-color:#d4edda; padding:20px; border-radius:10px; border:1px solid #c3e6cb">
                <h2 style="color:#155724; margin-top:0;">✅ Submission Successful!</h2>
                <p style="font-size:18px;">Thank you! Your logic has been recorded. To achieve full mastery of this topic, you should now discuss your reasoning with the Socratic AI Tutor.</p>
            </div>
        """, unsafe_allow_safe_html=True)
        
        st.write("")
        if st.button("💬 Open AI Socratic Tutor Now", use_container_width=True):
            st.session_state.current_nav = "🤖 Socratic Tutor"
            st.session_state.last_submission_success = False
            st.rerun()
        
        if st.button("⬅️ Back to Modules List"):
            st.session_state.last_submission_success = False
            st.rerun()
        return # Prevents showing the quiz again

    # --- STEP 2: Normal Module Listing ---
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        # Filter modules by student group
        modules = df[df['Group'] == student_group]
        
        if modules.empty:
            st.info("No modules assigned to your group yet.")
            return

        for idx, row in modules.iterrows():
            with st.expander(f"📖 Module {idx+1}: {row['Sub_Title']}", expanded=True):
                st.markdown(f"#### {row['Main_Title']}")
                st.write(f"**Objectives:** {row['Learning_Objectives']}")
                
                # Space-friendly engineering: Columns for PDF and Video
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.link_button("📄 View Study Material (PDF)", row['File_Links (PDF/Images)'], use_container_width=True)
                with c2:
                    st.link_button("📺 Watch Video Lecture", row['Video_Links'], use_container_width=True)

                st.divider()
                
                # Styling the Question: Large, Blue, and Numbered
                st.markdown(f"""
                    <h3 style="color: #1E3A8A; margin-bottom: 5px;">Question {idx+1}:</h3>
                    <p style="font-size: 20px; font-weight: 500;">{row['Diagnostic_Question']}</p>
                """, unsafe_allow_safe_html=True)

                # Diagnostic Tiers
                t1 = st.radio("Select your answer:", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                t2 = st.select_slider("How confident are you in this answer?", 
                                    options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                t3 = st.text_area("Explain your chemical reasoning (Why did you choose this?):", key=f"t3_{idx}")
                t4 = st.select_slider("How confident are you in your explanation?", 
                                    options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

                if st.button(f"Submit Module {idx+1} Diagnostic", key=f"btn_{idx}"):
                    # Save to DB
                    success = log_assessment(
                        st.session_state.user['User_ID'], 
                        student_group, 
                        row['Sub_Title'], t1, t2, t3, t4, "Complete", ""
                    )
                    if success:
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        log_temporal_trace(st.session_state.user['User_ID'], "SUBMIT_DIAGNOSTIC", row['Sub_Title'])
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_ai_chat(student_group):
    # Only allow experimental groups
    if student_group not in ["School A", "Exp_A"]:
        st.warning("⚠️ The Socratic AI Tutor is reserved for the Experimental Research Group.")
        return

    if 'current_topic' not in st.session_state:
        st.info("👋 Please complete a Diagnostic Check in 'Learning Modules' first to activate the Tutor.")
        return

    st.title(f"🤖 Socratic Tutor")
    st.caption(f"Topic: {st.session_state.current_topic}")

    # Initialize AI
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        # Using direct model path to fix v1beta 404
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    except Exception as e:
        st.error(f"AI Connection Error: {e}")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning to the tutor..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            # PhD Level Socratic Scaffolding Prompt
            system_prompt = (
                f"You are a PhD Socratic Tutor for Chemistry. Topic: {st.session_state.current_topic}. "
                f"Pedagogical Scaffolding Logic: {st.session_state.logic_tree}. "
                "Instructions: Never give the direct answer. If a student is wrong, ask a question "
                "about the underlying concept. Max 2 sentences per response."
            )
            
            response = model.generate_content(
                f"{system_prompt}\nStudent: {prompt}",
                request_options=RequestOptions(api_version='v1')
            )
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            log_temporal_trace(st.session_state.user['User_ID'], "AI_CONVERSATION_TURN", st.session_state.current_topic)
            
        except Exception as e:
            st.error(f"Handshake error: {e}")

def render_progress(uid):
    st.title("📈 Your Research Progress")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        
        if user_df.empty:
            st.info("Complete your first module to see progress data!")
            return

        # Professional Metrics Row
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Modules Attempted", len(user_df['Module_ID'].unique()))
        with c2:
            # Calculate total engagement turns from temporal traces
            traces_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            u_traces = traces_df[(traces_df['User_ID'].astype(str) == str(uid)) & (traces_df['Event'] == 'AI_CONVERSATION_TURN')]
            st.metric("Socratic Engagement", f"{len(u_traces)} Turns")
        with c3:
            st.metric("Current Status", "Active Researcher")

        # Confidence Growth Chart
        st.subheader("Metacognitive Confidence Growth")
        
        # Mapping confidence strings to numbers for plotting
        conf_map = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}
        user_df['Tier_2_Num'] = user_df['Tier_2 (Confidence_Ans)'].map(conf_map)
        user_df['Tier_4_Num'] = user_df['Tier_4 (Confidence_Reas)'].map(conf_map)
        
        fig = px.line(user_df, x='Timestamps', y=['Tier_2_Num', 'Tier_4_Num'], 
                      labels={"value": "Confidence Level (1-4)", "variable": "Assessment Stage"},
                      title="Pre-Reasoning vs. Post-Reasoning Confidence",
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading progress: {e}")
