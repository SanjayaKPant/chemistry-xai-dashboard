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
        st.stop()
        
    user, uid = st.session_state.user, st.session_state.user.get('User_ID')
    group = str(user.get('Group', 'School A')).strip()

    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = menu[0]

    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_tab))
    st.session_state.current_tab = choice

    if choice == "🏠 Dashboard":
        st.title(f"नमस्ते, {user['Name']}! 🙏")
        st.info("तपाईंको आजको लक्ष्य: मोड्युल पूरा गर्नुहोस् र साथी AI सँग छलफल गर्नुहोस्।")
    elif choice == "📚 Learning Modules":
        render_modules(uid, group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(uid, group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(uid)

# --- Find the render_modules function in your student_portal.py ---

def render_modules(uid, group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        # Check finished modules
        finished = []
        if not log_df.empty:
            finished = log_df[(log_df['User_ID'].astype(str) == str(uid)) & (log_df['Status'] == 'POST')]['Module_ID'].tolist()

        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        all_m = df[df['Group'] == group]
        active_module = next((row for _, row in all_m.iterrows() if row['Sub_Title'] not in finished), None)

        if active_module is None:
            st.success("🎉 उत्कृष्ट! तपाईंले सबै उपलब्ध मोड्युलहरू पूरा गर्नुभयो।")
            return

        m_id = active_module['Sub_Title']
        st.subheader(f"📖 {m_id}")
        
        # Mastery logic for Tiers 5 & 6
        if st.session_state.get(f"mastery_{m_id}"):
            st.success("🎯 Saathi AI has confirmed your understanding!")
            t5 = st.text_area("Tier 5: Revised Reasoning", key=f"t5_{m_id}")
            t6 = st.select_slider("Tier 6: New Confidence", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{m_id}")
            
            if st.button("Finalize & Save Mastery"):
                # FIXED: Call with all 13 research columns for the POST-test
                from database_manager import log_assessment
                log_assessment(uid, group, m_id, "REVISED", "N/A", "N/A", "N/A", "POST", get_nepal_time(), t5, t6, "Correct", "Resolved")
                st.session_state[f"mastery_{m_id}"] = False
                st.rerun()
        else:
            # Diagnostic Question UI
            st.write(f"**Question:** {active_module['Diagnostic_Question']}")
            t1 = st.radio("Answer (Tier 1)", [active_module['Option_A'], active_module['Option_B'], active_module['Option_C'], active_module['Option_D']], key=f"t1_{m_id}")
            t2 = st.select_slider("Confidence (Tier 2)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{m_id}")
            t3 = st.text_area("Reasoning (Tier 3)", key=f"t3_{m_id}")
            t4 = st.select_slider("Reasoning Confidence (Tier 4)", ["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{m_id}")

            if st.button("Submit & Start AI Discussion"):
                # THE CRITICAL FIX: Only send the first 9 arguments for INITIAL logs
                # The database_manager handles the rest as "N/A"
                from database_manager import log_assessment
                success = log_assessment(uid, group, m_id, t1, t2, t3, t4, "INITIAL", get_nepal_time())
                
                if success:
                    st.session_state.current_topic = m_id
                    st.session_state.active_module_data = active_module
                    st.session_state.logic_tree = active_module['Socratic_Tree']
                    st.session_state.current_tab = "🤖 साथी (Saathi) AI"
                    st.rerun()
                else:
                    st.error("Submission failed. Please check your internet connection.")

    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_ai_chat(uid, group):
    topic = st.session_state.get('current_topic')
    module_data = st.session_state.get('active_module_data')

    if not topic or not module_data:
        st.warning("पहिले मोड्युलमा गएर उत्तर दिनुहोस्।")
        return

    # --- NEW SIDE-BY-SIDE LAYOUT ---
    col_ref, col_chat = st.columns([1, 2])

    with col_ref:
        st.subheader("📍 Reference Module")
        st.markdown(f"**Concept:** {topic}")
        st.info(f"**Question:** {module_data['Diagnostic_Question']}")
        st.write(f"A) {module_data['Option_A']}\n\nB) {module_data['Option_B']}\n\nC) {module_data['Option_C']}\n\nD) {module_data['Option_D']}")
        if module_data.get('File_Link'):
            st.markdown(f"[📄 Study Material]({module_data['File_Link']})")

    with col_chat:
        st.subheader("🤖 साथी (Saathi) AI")
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "system", "content": f"Socratic Tutor. Goal: {st.session_state.get('logic_tree')}. Use Nepali/Roman Nepali."}]

        for m in st.session_state.messages:
            if m["role"] != "system":
                with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Ask Saathi AI..."):
            # FIX: Display student prompt immediately
            with st.chat_message("user"): st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
            ai_reply = response.choices[0].message.content
            
            if "[MASTERY_DETECTED]" in ai_reply:
                st.session_state[f"mastery_{topic}"] = True
                st.session_state.current_tab = "📚 Learning Modules"
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                st.rerun()
            
            with st.chat_message("assistant"): st.markdown(ai_reply)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})

def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति")
    st.write("Confidence vs Accuracy trends will appear here.")
