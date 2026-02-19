import streamlit as st
import pandas as pd
import google.generativeai as genai
from database_manager import get_gspread_client, log_student_response, log_temporal_trace

# --- RESEARCH-GRADE SOCRATIC SYSTEM PROMPT ---
SOCRATIC_PROMPT = """
You are a Socratic Chemistry Tutor designed for Grade 10 students in Nepal. 
Your goal is to guide students toward conceptual clarity using the National Curriculum standards.

SCIENTIFIC APPROACH:
1. Ground questions in molecular behavior, periodic trends (Modern Periodic Law), and sub-shell electronic configuration (Aufbau's Principle)[cite: 31, 69].
2. Address specific textbook concepts: Metals/Non-metals, Alkali/Alkaline Earth metals, and Halogens[cite: 46, 81].
3. Scaffolding: Use the 'Socratic_Tress' guidance from the teacher to identify specific logical hurdles.

ETHICAL GUIDELINES:
- Never provide the final answer or chemical formulas directly.
- Use encouraging language to reduce 'Science Anxiety' in young researchers.
"""

def show():
    if 'user' not in st.session_state:
        st.error("Please log in again to continue your session.")
        return

    user = st.session_state.user
    # Matching Sheet header: 'Group'
    user_group = user.get('Group', 'Control')
    user_role = user.get('Role', 'Student')
    
    st.sidebar.title(f"👤 {user.get('Name', 'Researcher')}")
    st.sidebar.info(f"Group: {user_group} | Role: {user_role}")
    
    # Navigation logic for PhD experimental vs control groups
    menu = ["📚 Science Modules", "🤖 Socratic Tutor", "📊 My Progress"]
    if user_group == "Control":
        menu = ["📚 Digital Library", "📊 My Progress"]
        
    choice = st.sidebar.radio("Research Navigation", menu)

    if choice in ["📚 Science Modules", "📚 Digital Library"]:
        render_learning_path(user_group, user_role)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        # Fixed 'User_ID' mapping for logs
        render_progress(user.get('User_ID'))

def render_learning_path(group, role):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        # Data Cleaning for robust mapping
        df.columns = [c.strip().replace(' ', '_') for c in df.columns]

        # RESEARCH ACCESS: Teachers see all content for validation; Students only their group
        if role in ['Teacher', 'Head Teacher', 'Science Teacher']:
            my_data = df
        else:
            my_data = df[df['Group'] == group]

        if not my_data.empty:
            for idx, row in my_data.iterrows():
                with st.expander(f"🔹 {row.get('Sub-Title', 'Unnamed Module')}"):
                    st.write(f"**Objectives:** {row.get('Learning_Objectives', 'N/A')}")
                    
                    if row.get('Video_Links'):
                        for link in str(row['Video_Links']).split('\n'):
                            if "http" in link: st.video(link.strip())

                    st.markdown("---")
                    st.info(f"**Diagnostic Question:**\n\n{row.get('Four_Tier_Data', 'Assessment pending.')}")
                    
                    with st.form(key=f"chem_form_{idx}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            t1 = st.radio("Answer Choice", ["A", "B", "C", "D"], key=f"t1_{idx}")
                            t2 = st.select_slider("Confidence (Tier 2)", ["Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                        with c2:
                            t3 = st.text_area("Justification (Tier 3)", key=f"t3_{idx}", placeholder="Explain the molecular process...")
                            t4 = st.select_slider("Confidence (Tier 4)", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                        
                        if st.form_submit_button("Submit Response"):
                            user_id = st.session_state.user.get('User_ID')
                            log_student_response(user_id, row['Sub-Title'], group, t1, t2, t3, t4)
                            
                            # Save state for the AI Session
                            st.session_state.current_pivot = row.get('Socratic_Tress', "Explore chemical principles.")
                            st.session_state.current_sub = row['Sub-Title']
                            st.session_state.last_justification = t3
                            st.success("✅ Saved! Proceed to 'Socratic Tutor' to refine your understanding.")
        else:
            st.warning("No curriculum modules are currently assigned to your group.")
    except Exception as e:
        st.error(f"Module Load Error: {e}")

# --- AI CORE CONFIGURATION ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Fix: Using stable model name 'gemini-1.5-flash-latest' to prevent 404 errors
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            system_instruction=SOCRATIC_PROMPT
        )
    else:
        st.error("API Error: GEMINI_API_KEY not found in Streamlit Secrets.")
except Exception as e:
    st.error(f"AI Engine Error: {e}")

def render_socratic_tutor():
    st.subheader("🤖 Socratic Reasoning Assistant")

    if 'last_justification' not in st.session_state:
        st.info("💡 Please complete a 'Science Module' first to begin a tutoring session.")
        return

    concept = st.session_state.get('current_sub', "Chemistry")
    pivot_instruction = st.session_state.get('current_pivot', "Standard scaffolding")
    student_thought = st.session_state.get('last_justification', "")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"I see your thoughts on **{concept}**: *'{student_thought}'*. Based on atomic principles, why do you believe this occurs?"
        })

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # The 'Hidden' Research Prompt
        research_context = (
            f"Curriculum Focus: {concept}. Teacher's Scaffolding Logic: {pivot_instruction}. "
            f"Student said: {prompt}. Apply Socratic Method."
        )

        try:
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]
            ])
            response = chat.send_message(research_context)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Critical for PhD Analysis: Logging temporal engagement
            log_temporal_trace(st.session_state.user.get('User_ID'), "AI_CHAT_INTERACTION", f"Concept: {concept}")
            
        except Exception as e:
            st.error(f"Tutoring Connection Error: {e}")

def render_progress(uid):
    st.subheader("📊 Your Research Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        # Clean UID filtering
        user_df = df[df['User_ID'] == uid]
        if not user_df.empty:
            st.dataframe(user_df, use_container_width=True)
        else:
            st.info("Begin your modules to see your progress logs here.")
    except Exception as e:
        st.error(f"Data Fetching Error: {e}")
