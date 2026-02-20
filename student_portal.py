import streamlit as st
import pandas as pd
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

# --- RESEARCH-GRADE SOCRATIC SYSTEM PROMPT ---
SOCRATIC_PROMPT = """
You are a Socratic Chemistry Tutor designed for Grade 10 students in Nepal. 
Your goal is to guide students toward conceptual clarity using the National Curriculum standards.

SCIENTIFIC APPROACH:
1. Ground questions in molecular behavior, periodic trends (Modern Periodic Law), and sub-shell electronic configuration (Aufbau's Principle).
2. Address specific textbook concepts: Metals/Non-metals, Alkali/Alkaline Earth metals, and Halogens.
3. Scaffolding: Use the 'Socratic_Tree' guidance from the teacher to identify logical hurdles.

ETHICAL GUIDELINES:
- Never provide the final answer or chemical formulas directly.
- Use encouraging language to reduce 'Science Anxiety'.
"""

def show():
    if 'user' not in st.session_state:
        st.error("Please log in again.")
        return

    user = st.session_state.user
    # Standardizing Group name and User ID
    user_school = str(user.get('Group', 'School B')).strip()
    user_id = user.get('User_ID')
    
    st.sidebar.title(f"👤 {user.get('Name', 'Student')}")
    st.sidebar.info(f"🏫 {user_school} | ID: {user_id}")
    
    # NAVIGATION LOGIC: School A gets the AI Tutor (Experimental), School B is Control
    menu = ["📚 Digital Library", "📊 My Progress"]
    if "SCHOOL A" in user_school.upper():
        menu = ["📚 Digital Library", "🤖 Socratic Tutor", "📊 My Progress"]
        
    choice = st.sidebar.radio("Research Navigation", menu)

    if choice == "📚 Digital Library":
        render_learning_path(user_school)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        render_progress(user_id)

def render_learning_path(school):
    st.subheader("📖 Chemistry Digital Library")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        
        raw_data = ws.get_all_values()
        if len(raw_data) < 2:
            st.info("No lessons have been deployed yet.")
            return

        # Header Normalization
        headers = [str(h).strip().upper().replace(" ", "_") for h in raw_data[0]]
        df = pd.DataFrame(raw_data[1:], columns=headers)

        if 'GROUP' in df.columns:
            my_data = df[df['GROUP'].str.strip().str.upper() == school.upper()]
        else:
            st.error("Column 'Group' not found in spreadsheet.")
            return

        if not my_data.empty:
            for idx, row in my_data.iterrows():
                title = row.get('SUB_TITLE', 'Unnamed Concept')
                with st.expander(f"🔹 {title}"):
                    st.write(f"**Objectives:** {row.get('LEARNING_OBJECTIVES', 'N/A')}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if row.get('FILE_LINKS'): st.link_button("📄 View PDF", row['FILE_LINKS'])
                    with c2:
                        if row.get('VIDEO_LINKS'): st.link_button("🎥 Watch Video", row['VIDEO_LINKS'])

                    st.markdown("---")
                    st.write("🧪 **4-Tier Diagnostic Assessment**")
                    
                    with st.form(key=f"tier_form_{idx}"):
                        t1 = st.radio("Tier 1: Answer", ["A", "B", "C", "D"], key=f"t1_{idx}")
                        t2 = st.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                        t3 = st.text_area("Tier 3: Reasoning", key=f"t3_{idx}")
                        t4 = st.select_slider("Tier 4: Confidence", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                        
                        if st.form_submit_button("Submit Response"):
                            success = log_assessment(
                                user_id=st.session_state.user['User_ID'], 
                                group=school, 
                                module_id=title, 
                                t1=t1, t2=t2, t3=t3, t4=t4, 
                                diag="Logged", 
                                misc="N/A"
                            )
                            if success:
                                st.session_state.current_sub = title
                                st.session_state.current_tree = row.get('SOCRATIC_TREE', "")
                                st.session_state.last_justification = t3
                                st.success("✅ Logged! Proceed to Socratic Tutor if available.")
        else:
            st.warning(f"No modules assigned to {school}.")
    except Exception as e:
        st.error(f"Module Load Error: {e}")

# --- AI CORE CONFIGURATION ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=SOCRATIC_PROMPT)
except:
    pass

def render_socratic_tutor():
    st.subheader("🤖 Socratic Reasoning Assistant")
    if 'last_justification' not in st.session_state:
        st.info("💡 Complete a module assessment first.")
        return

    concept = st.session_state.get('current_sub', "Chemistry")
    tree_logic = st.session_state.get('current_tree', "")
    student_thought = st.session_state.get('last_justification', "")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"You noted: *'{student_thought}'*. Regarding **{concept}**, why do you believe that is the case?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        research_context = f"Topic: {concept}. Teacher Logic: {tree_logic}. Student Response: {prompt}."
        try:
            chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
            response = chat.send_message(research_context)
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            log_temporal_trace(st.session_state.user['User_ID'], "AI_CHAT", concept)
        except Exception as e:
            st.error(f"Chat Error: {e}")

def render_progress(uid):
    st.subheader("📊 Your Research Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        st.dataframe(user_df, use_container_width=True)
    except:
        st.error("Progress log unavailable.")
