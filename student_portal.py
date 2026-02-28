import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- 1. RESEARCH HELPERS (NEPAL TIME) ---
def get_nepal_time():
    """VPS Requirement: Precise timestamping for Nepal-based research (UTC +5:45)."""
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first)")
        st.stop()
        
    user = st.session_state.user
    uid = user.get('User_ID')
    group = str(user.get('Group', 'School A')).strip()

    # SIDEBAR NAVIGATION
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {group}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = menu[0]

    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_tab))
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(uid, group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid, group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)

# --- 2. DASHBOARD ---
def render_dashboard(user):
    st.title(f"नमस्ते, {user['Name']}! 🙏")
    st.markdown("### साथी (Saathi) AI सिकाई पोर्टल")
    st.info("तपाईंको आजको लक्ष्य: मोड्युल पूरा गर्नुहोस् र साथी AI सँग छलफल गर्नुहोस्।")
    

def render_modules(uid, group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # 1. Fetch logs to identify completed modules (Status: POST)
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        finished_modules = []
        if not log_df.empty:
            finished_modules = log_df[(log_df['User_ID'].astype(str) == str(uid)) & (log_df['Status'] == 'POST')]['Module_ID'].tolist()

        # 2. Fetch available modules for this group
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        all_modules = df[df['Group'] == group]

        if all_modules.empty:
            st.warning("तपाईंको समूहको लागि कुनै मोड्युलहरू छैनन्।")
            return

        # 3. Find first uncompleted module
        active_row = None
        for _, row in all_modules.iterrows():
            if row['Sub_Title'] not in finished_modules:
                active_row = row
                break 

        if active_row is None:
            st.success("🎉 सबै मोड्युलहरू पूरा भए! राम्रो काम गर्नुभयो।")
            return

        m_id = active_row['Sub_Title']
        st.subheader(f"📖 {m_id}")
        
        # Display Objectives and Materials
        with st.expander("Learning Objectives & Materials", expanded=True):
            st.write(f"**Objectives:** {active_row.get('Objectives', 'Explore this scientific concept.')}")
            if active_row.get('File_Link'):
                st.markdown(f"[📄 Download Study Material]({active_row['File_Link']})")

        # --- INITIAL MODE (Tiers 1-4) ---
        st.info("💡 पहिले यो प्रश्नको उत्तर दिनुहोस् र आफ्नो तर्क लेख्नुहोस्। त्यसपछि साथी AI सँग छलफल सुरु हुनेछ।")
        st.write(f"**Diagnostic Question:** {active_row['Diagnostic_Question']}")
        
        opts = [active_row['Option_A'], active_row['Option_B'], active_row['Option_C'], active_row['Option_D']]
        t1 = st.radio("तपाईंको उत्तर (Tier 1 Choice)", opts, key=f"t1_{m_id}")
        t2 = st.select_slider("तपाईं यो उत्तरमा कत्तिको विश्वस्त हुनुहुन्छ? (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{m_id}")
        t3 = st.text_area("तपाईंले किन यो उत्तर रोज्नुभयो? (Tier 3 Reasoning)", key=f"t3_{m_id}", placeholder="आफ्नो तर्क यहाँ लेख्नुहोस्...")
        t4 = st.select_slider("तपाईं आफ्नो तर्कमा कत्तिको विश्वस्त हुनुहुन्छ? (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{m_id}")

        if st.button("Submit & Start AI Discussion", key=f"btn_{m_id}"):
            if not t3 or len(t3.strip()) < 5:
                st.error("❌ कृपया छलफल सुरु गर्नको लागि आफ्नो तर्क (Tier 3) लेख्नुहोस्।")
            else:
                # Log INITIAL Data
                log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                
                # THE CONTEXT BRIDGE: Save module data and pre-seed the Chat
                st.session_state.active_module = active_row.to_dict()
                
                # Pre-seeding the message list ensures AI knows everything from the start
                st.session_state.messages = [
                    {"role": "system", "content": f"{SOCRATIC_NORMS}\nTarget Logic Tree: {active_row['Socratic_Tree']}"},
                    {"role": "assistant", "content": f"Namaste! I see you chose **'{t1}'** because: *'{t3}'*. That is a great starting point! Let's explore your reasoning together. Why do you think that specific option fits better than the others in this scientific scenario?"}
                ]
                
                # Redirect to Chat Tab
                st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                st.rerun()

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_ai_chat(uid, group):
    # Check if a module has been started
    module = st.session_state.get('active_module')
    
    if not module:
        st.warning("⚠️ पहिले 'Learning Modules' मा गएर कुनै प्रश्नको उत्तर दिनुहोस्। (Please answer a question in Learning Modules first.)")
        return

    # --- THE 360° SPLIT-SCREEN UI ---
    col_phenomenon, col_inquiry = st.columns([1, 1.5], gap="large")

    # LEFT COLUMN: Scientific Context (Scaffolding)
    with col_phenomenon:
        st.markdown("### 📝 Scientific Context")
        with st.container(border=True):
            st.subheader(module['Sub_Title'])
            st.info(f"**Question:**\n{module['Diagnostic_Question']}")
            st.write("---")
            st.write(f"**A)** {module['Option_A']}")
            st.write(f"**B)** {module['Option_B']}")
            st.write(f"**C)** {module['Option_C']}")
            st.write(f"**D)** {module['Option_D']}")
        st.caption("Keep this question in mind while discussing with Saathi AI.")

    # RIGHT COLUMN: Socratic Inquiry & Mastery Detection
    with col_inquiry:
        st.subheader("🤖 Inquiry with Saathi AI")
        
        # Check if mastery was triggered during the chat
        if st.session_state.get('mastery_triggered'):
            st.balloons()
            render_revision_form(uid, group, module)
            return

        # Display Chat History
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "system", "content": SOCRATIC_NORMS}]

        for m in st.session_state.messages[1:]:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        # Chat Input logic
        if prompt := st.chat_input("Explain your logic to Saathi..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Micro-genetic log
            log_temporal_trace(uid, "CHAT_MSG", f"Topic: {module['Sub_Title']} | Msg: {prompt}")
            
            # API Call to GPT-4o
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
            ai_reply = response.choices[0].message.content
            
            # Mastery Logic
            if "[MASTERY_DETECTED]" in ai_reply:
                st.session_state.mastery_triggered = True
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()

# --- HELPER: TIER 5 & 6 FORM (Inside the AI Tab) ---
def render_revision_form(uid, group, module):
    st.success("🌟 Mastery Detected! / बधाई छ! तपाईंले अवधारणा बुझ्नुभयो।")
    st.markdown("### Post-Discussion Assessment (Tier 5 & 6)")
    st.write("साथी AI सँगको छलफलपछि, के तपाईं आफ्नो उत्तर वा तर्क परिवर्तन गर्न चाहनुहुन्छ?")
    
    with st.form("t56_form"):
        opts = [module['Option_A'], module['Option_B'], module['Option_C'], module['Option_D']]
        t5 = st.radio("तपाईंको अन्तिम उत्तर (Tier 5 Final Choice):", opts)
        t6 = st.select_slider("तपाईं अहिले कत्तिको विश्वस्त हुनुहुन्छ? (Tier 6 Final Confidence):", ["Guessing", "Unsure", "Sure", "Very Sure"])
        t_feedback = st.text_area("तपाईंको सोचाइमा के परिवर्तन आयो? (Optional Reflection):")
        
        if st.form_submit_button("Complete Module & Save"):
            # Log Final POST data to Google Sheets
            log_assessment(uid, group, module['Sub_Title'], "N/A", "N/A", t_feedback, "N/A", "POST", 
                           get_nepal_time(), t5, t6)
            
            # Reset states for the next module
            st.session_state.active_module = None
            st.session_state.mastery_triggered = False
            st.session_state.messages = []
            st.session_state.current_tab = "🏠 Dashboard"
            st.rerun()

# --- 5. PROGRESS ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress)")
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, thickness=20, label=["Initial Guess", "Initial Sure", "Final Unsure", "Final Mastery"], color="#2E86C1"),
        link = dict(source=[0, 1, 0, 1], target=[2, 3, 3, 2], value=[2, 5, 3, 1])
    )])
    st.plotly_chart(fig, width='stretch')
