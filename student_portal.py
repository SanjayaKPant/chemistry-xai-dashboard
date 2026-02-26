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
        
        # 1. LOAD AND CLEAN LOGS (Fixed for cross-account bug)
        all_logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        finished_modules = []
        
        if not all_logs.empty:
            # Force everything to string and strip spaces to ensure a perfect match
            all_logs['User_ID'] = all_logs['User_ID'].astype(str).str.strip().str.upper()
            all_logs['Status'] = all_logs['Status'].astype(str).str.strip().str.upper()
            
            finished_modules = all_logs[
                (all_logs['User_ID'] == str(uid).strip().upper()) & 
                (all_logs['Status'] == 'POST')
            ]['Module_ID'].unique().tolist()

        # 2. LOAD MATERIALS
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        # Filter modules assigned to this student's specific research group
        available_modules = df[df['Group'].astype(str).str.strip() == str(group).strip()]

        # 3. FIND ACTIVE MODULE
        active_module = next((row for _, row in available_modules.iterrows() 
                             if str(row['Sub_Title']) not in finished_modules), None)

        if active_module is None:
            st.success("🎉 उत्कृष्ट! तपाईंले सबै उपलब्ध मोड्युलहरू पूरा गर्नुभयो।")
            return

        # 4. DISPLAY MODULE WITH NUMBERING
        # Use the 'Module_No' column from your spreadsheet
        m_no = active_module.get('Module_No', '?')
        m_id = active_module['Sub_Title']
        st.subheader(f"📖 Module {m_no}: {m_id}")
        
        # UI for tiers remains the same...
        # Ensure st.session_state.active_module_data = active_module is set on submit

    except Exception as e:
        st.error(f"Module Loading Error: {e}")

def render_ai_chat(uid, group):
    topic = st.session_state.get('current_topic')
    module_data = st.session_state.get('active_module_data')

    if topic is None or module_data is None:
        st.warning("कृपया पहिले मोड्युल सुरु गर्नुहोस्।")
        return

    # Layout for context-aware chatting
    col_ref, col_chat = st.columns([1, 2])
    # [Your col_ref code here...]

    with col_chat:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "system", "content": "Socratic Tutor Logic..."}]

        for m in st.session_state.messages:
            if m["role"] != "system":
                with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("साथी AI लाई सोध्नुहोस्..."):
            with st.chat_message("user"): st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
                ai_reply = response.choices[0].message.content
                
                # RECTIFICATION: Save ACTUAL chat details to Temporal Traces
                # Format: "Student: [msg] | AI: [reply]"
                full_interaction = f"Student: {prompt} || Saathi: {ai_reply}"
                log_temporal_trace(str(uid), f"CHAT_SESSION_{topic}", full_interaction)

                if "[MASTERY_DETECTED]" in ai_reply:
                    st.session_state[f"mastery_{topic}"] = True
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.session_state.current_tab = "📚 Learning Modules"
                    st.rerun()

                with st.chat_message("assistant"): st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})

            except Exception as e:
                st.error(f"AI Error: {e}")

def render_ai_chat(uid, group):
    topic = st.session_state.get('current_topic')
    module_data = st.session_state.get('active_module_data')

    if topic is None or module_data is None:
        st.warning("Please start a module first.")
        return

    # Layout
    col_ref, col_chat = st.columns([1, 2])
    # ... [col_ref display code remains same] ...

    with col_chat:
        # Chat history display
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "system", "content": "Socratic Tutor..."}]

        for m in st.session_state.messages:
            if m["role"] != "system":
                with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("साथी AI लाई सोध्नुहोस्..."):
            with st.chat_message("user"): st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
                ai_reply = response.choices[0].message.content
                
                # RECTIFICATION: Save the ACTUAL chat content to Temporal Traces
                chat_details = f"User: {prompt} | AI: {ai_reply}"
                log_temporal_trace(uid, f"CHAT_{topic}", chat_details)

                if "[MASTERY_DETECTED]" in ai_reply:
                    st.session_state[f"mastery_{topic}"] = True
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.session_state.current_tab = "📚 Learning Modules"
                    st.rerun()

                with st.chat_message("assistant"): st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})

            except Exception as e:
                st.error(f"AI Error: {e}")

def render_ai_chat(uid, group):
    topic = st.session_state.get('current_topic')
    module_data = st.session_state.get('active_module_data')

    # FIX 1: Safe check for None or Empty Series
    if topic is None or module_data is None:
        st.warning("पहिले मोड्युलमा गएर उत्तर दिनुहोस्। (Please start a module first.)")
        return

    # --- SIDE-BY-SIDE LAYOUT ---
    col_ref, col_chat = st.columns([1, 2])

    with col_ref:
        st.subheader("📍 Reference Module")
        # FIX 2: Using .get() to prevent KeyError if a column name is slightly different
        q_text = module_data.get('Diagnostic_Question', 'Question not found')
        st.info(f"**Concept:** {topic}")
        st.markdown(f"**Question:**\n{q_text}")
        
        # Display options only if they exist
        for opt in ['Option_A', 'Option_B', 'Option_C', 'Option_D']:
            val = module_data.get(opt, "")
            if val: st.write(f"- {val}")
        
        # Safe link retrieval
        file_link = module_data.get('File_Link')
        if pd.notna(file_link) and str(file_link).startswith("http"):
            st.markdown(f"[📄 View Study Material]({file_link})")

    with col_chat:
        st.subheader("🤖 साथी (Saathi) AI")
        
        if "messages" not in st.session_state:
            # Socratic Prompt Engineering
            logic = st.session_state.get('logic_tree', 'Guide the student using Socratic questioning.')
            st.session_state.messages = [{
                "role": "system", 
                "content": f"You are Saathi, a Socratic Chemistry Tutor. Logic Path: {logic}. "
                           "Use Nepali/Roman Nepali. If they reach mastery, include '[MASTERY_DETECTED]'."
            }]

        # Display history
        for m in st.session_state.messages:
            if m["role"] != "system":
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        # Chat Input
        if prompt := st.chat_input("साथी AI लाई सोध्नुहोस्..."):
            # UI Fix: Immediate user message display
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                # FIX 3: Using gpt-4o or gpt-4o-mini consistently
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=st.session_state.messages
                )
                ai_reply = response.choices[0].message.content
                
                if "[MASTERY_DETECTED]" in ai_reply:
                    st.session_state[f"mastery_{topic}"] = True
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.balloons()
                    st.success("🎯 Mastery Detected! Re-directing...")
                    st.session_state.current_tab = "📚 Learning Modules"
                    st.rerun()

                with st.chat_message("assistant"):
                    st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
                # Trace log for research
                log_temporal_trace(uid, "AI_CHAT", f"Topic: {topic}")

            except Exception as e:
                st.error(f"AI Error: {e}")
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति")
    st.write("Confidence vs Accuracy trends will appear here.")
