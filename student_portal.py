import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- 1. RESEARCH CONSTANTS (THE AI BRAIN) ---
# Defining this at the top prevents the 'NameError'
SOCRATIC_NORMS = """
You are Saathi AI, a Socratic Chemistry Tutor for high school students in Nepal.

RESEARCH GOAL: Facilitate conceptual change by identifying and resolving scientific misconceptions.

OPERATIONAL RULES:
1. STRICT ADHERENCE: Never provide direct answers or confirm correctness immediately.
2. CONTEXT UTILIZATION: Start the conversation by acknowledging the student's Tier 1 choice and Tier 3 reasoning.
3. PROBING: Ask one question at a time. Focus on the 'why' and 'how' of the chemical phenomenon.
4. BILINGUAL FLEXIBILITY: Use English or Nepali (Romanized or Devanagari) as per student preference.
5. MASTERY TRIGGER: If the student demonstrates a scientifically accurate mental model and explains the logic correctly, you MUST output the code: [MASTERY_DETECTED]
"""

def get_nepal_time():
    """UTC +5:45 for precise research timestamping."""
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

# --- 2. MAIN NAVIGATION CONTROL ---
def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first)")
        st.stop()
        
    user = st.session_state.user
    uid = str(user.get('User_ID')).upper()
    group = str(user.get('Group', 'School A')).strip()

    # Sidebar UI
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {group}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = menu[0]

    # Sidebar Navigation Sync
    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_tab))
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard": render_dashboard(user)
    elif choice == "📚 Learning Modules": render_modules(uid, group)
    elif choice == "🤖 साथी (Saathi) AI": render_ai_chat(uid, group)
    elif choice == "📈 My Progress": render_metacognitive_dashboard(uid)

def render_dashboard(user):
    st.title(f"Namaste, {user.get('Name')}! 🙏")
    st.markdown("---")
    st.info("Goal: Complete the diagnostic questions in **'Learning Modules'** to unlock your Socratic discussion with Saathi AI.")

# --- 3. UPDATED MODULES (WITH ROBUST USER PARTITIONING) ---
def render_modules(uid, group):
    st.header("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # 1. Identify completed modules ONLY for THIS specific UID
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        finished_modules = []
        if not log_df.empty:
            # SAFETY: Strip spaces from headers and values to prevent cross-user blocking
            log_df.columns = [c.strip() for c in log_df.columns]
            user_mask = (log_df['User_ID'].astype(str).str.upper().str.strip() == uid.strip().upper())
            status_mask = (log_df['Status'].astype(str).str.strip() == 'POST')
            
            finished_modules = log_df[user_mask & status_mask]['Module_ID'].astype(str).str.strip().tolist()

        # 2. Load available modules for this specific Group
        m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        # SAFETY: Strip group names to ensure exact matching
        available = m_df[m_df['Group'].astype(str).str.strip() == group.strip()]

        if available.empty:
            st.warning(f"No modules found for group: {group}")
            return

        active_row = None
        for _, row in available.iterrows():
            # Check if this specific module title is in THIS user's finished list
            if str(row['Sub_Title']).strip() not in finished_modules:
                active_row = row
                break 

        if active_row is None:
            st.success("🎉 All modules complete for your account! / तपाईंको लागि सबै मोड्युलहरू पूरा भए!")
            return

        # --- THE REST OF THE TIER 1-4 LOGIC REMAINS UNCHANGED ---
        m_id = active_row['Sub_Title']
        st.subheader(f"📖 Concept: {m_id}")
        with st.expander("Learning Objectives", expanded=True):
            st.write(active_row.get('Objectives', 'Explore this concept.'))

        st.write(f"**Diagnostic Question:**\n{active_row['Diagnostic_Question']}")
        opts = [active_row['Option_A'], active_row['Option_B'], active_row['Option_C'], active_row['Option_D']]
        t1 = st.radio("तपाईंको उत्तर (Tier 1 Choice):", opts, key=f"t1_{m_id}")
        t2 = st.select_slider("आत्मविश्वास (Tier 2):", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{m_id}")
        t3 = st.text_area("तपाईंले किन यो उत्तर रोज्नुभयो? (Tier 3 Reasoning):", key=f"t3_{m_id}")
        t4 = st.select_slider("तर्कमा आत्मविश्वास (Tier 4):", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{m_id}")

        if st.button("Submit & Start Discussion"):
            if len(t3.strip()) < 5:
                st.error("❌ Please provide reasoning to continue.")
            else:
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                st.session_state.active_module = active_row.to_dict()
                st.session_state.messages = [
                    {"role": "system", "content": SOCRATIC_NORMS},
                    {"role": "assistant", "content": f"Namaste! I see you chose **'{t1}'** because: *'{t3}'*. Let's explore that logic..."}
                ]
                st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

# --- 4. UPDATED SAATHI AI (RECORDING BOTH CHANNELS) ---
def render_ai_chat(uid, group):
    module = st.session_state.get('active_module')
    if not module:
        st.warning("⚠️ Please submit an initial answer in 'Learning Modules' first.")
        return

    col_phenom, col_chat = st.columns([1, 1.5], gap="large")

    with col_phenom:
        st.markdown("### 📝 Current Phenomenon")
        with st.container(border=True):
            st.subheader(module['Sub_Title'])
            st.write(f"**Q:** {module['Diagnostic_Question']}")
            st.write("---")
            st.write(f"A) {module['Option_A']}\n\nB) {module['Option_B']}\n\nC) {module['Option_C']}\n\nD) {module['Option_D']}")

    with col_chat:
        if st.session_state.get('mastery_triggered'):
            st.balloons()
            render_revision_form(uid, group, module)
            return

        st.subheader("🤖 Socratic Discussion")
        for m in st.session_state.messages[1:]:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Explain your logic to Saathi..."):
            # 1. Append Student Message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner("Analyzing your logic..."):
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                resp = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
                ai_msg = resp.choices[0].message.content
                
                # 2. Record BOTH to Temporal Traces for Research
                # Log Student Message
                log_temporal_trace(uid, "CHAT_MSG", f"Topic: {module['Sub_Title']} | Student: {prompt}")
                # Log AI Message
                log_temporal_trace(uid, "CHAT_MSG", f"Topic: {module['Sub_Title']} | Saathi AI: {ai_msg}")
                
                if "[MASTERY_DETECTED]" in ai_msg:
                    st.session_state.mastery_triggered = True
                
                st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                st.rerun()

# --- 5. TIER 5 & 6 (POST-DISCUSSION REVISION) ---
def render_revision_form(uid, group, module):
    st.success("🌟 Mastery Detected! / अवधारणा स्पष्ट भयो।")
    with st.form("t56_form"):
        st.markdown("### Final Assessment")
        opts = [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']]
        t5 = st.radio("Final Choice (Tier 5):", opts)
        t6 = st.select_slider("Final Confidence (Tier 6):", ["Guessing", "Unsure", "Sure", "Very Sure"])
        reflection = st.text_area("What changed in your thinking?")
        
        if st.form_submit_button("Save & Complete"):
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", reflection, "N/A", "POST", 
                           get_nepal_time(), t5, t6)
            st.session_state.active_module = None
            st.session_state.mastery_triggered = False
            st.session_state.messages = []
            st.session_state.current_tab = "🏠 Dashboard"
            st.rerun()

# --- 6. PROGRESS DASHBOARD ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress Dashboard)")
    st.markdown("---")

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if log_df.empty:
            st.info("No data available yet. Start a learning module to see your progress!")
            return

        # Filter for current user
        user_data = log_df[log_df['User_ID'].astype(str).str.upper() == uid.upper()].copy()
        
        if user_data.empty:
            st.info("Complete your first module to unlock analytics.")
            return

        # 1. TOP LEVEL METRICS
        total_attempts = len(user_data)
        mastered_count = len(user_data[user_data['Status'] == 'POST'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Modules Explored", total_attempts)
        m2.metric("Concepts Mastered", mastered_count)
        m3.metric("Nepal Time", get_nepal_time().split()[1])

        st.markdown("### 🧬 Conceptual Growth Analysis")
        
        # 2. CONFIDENCE EVOLUTION (Tier 2/4 vs Tier 6)
        # Mapping confidence strings to numerical values for plotting
        conf_map = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}
        
        # We look for rows where we have both INITIAL and POST data
        # For a PhD design, we want to see if confidence increases after Saathi AI's intervention
        
        plot_data = []
        for module in user_data['Module_ID'].unique():
            mod_rows = user_data[user_data['Module_ID'] == module]
            initial = mod_rows[mod_rows['Status'] == 'INITIAL']
            post = mod_rows[mod_rows['Status'] == 'POST']
            
            if not initial.empty and not post.empty:
                plot_data.append({
                    "Module": module,
                    "Stage": "Before Saathi",
                    "Confidence": conf_map.get(initial.iloc[0]['T2'], 1)
                })
                plot_data.append({
                    "Module": module,
                    "Stage": "After Saathi",
                    "Confidence": conf_map.get(post.iloc[0]['T6'], 1)
                })

        if plot_data:
            df_viz = pd.DataFrame(plot_data)
            fig_conf = px.line(df_viz, x="Stage", y="Confidence", color="Module", 
                               markers=True, title="Confidence Gain per Concept",
                               labels={"Confidence": "Certainty Level (1-4)"})
            fig_conf.update_layout(yaxis=dict(tickmode='array', tickvals=[1,2,3,4], 
                                             ticktext=["Guessing", "Unsure", "Sure", "Very Sure"]))
            st.plotly_chart(fig_conf, use_container_width=True)
        
        # 3. RECENT ACTIVITY LOG
        st.markdown("### 📝 Learning Journal")
        display_df = user_data[['Timestamp', 'Module_ID', 'Status', 'T1', 'T5']].sort_values(by='Timestamp', ascending=False)
        display_df.columns = ["Time", "Concept", "Phase", "Initial Choice", "Final Choice"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
