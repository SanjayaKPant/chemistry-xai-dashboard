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
3. Scaffolding: Use the 'Socratic_Tree' guidance provided in the context to identify specific logical hurdles.

ETHICAL GUIDELINES:
- Never provide the final answer or chemical formulas directly.
- Use encouraging language to reduce 'Science Anxiety' in young researchers.
"""

def show():
    if 'user' not in st.session_state:
        st.error("Please log in again to continue your session.")
        return

    user = st.session_state.user
    # Matching Sheet header: 'Group' (School A or School B)
    user_school = user.get('Group', 'School B')
    user_role = user.get('Role', 'Student')
    user_id = user.get('User_ID')
    
    st.sidebar.title(f"👤 {user.get('Name', 'Researcher')}")
    st.sidebar.info(f"🏫 {user_school} | ID: {user_id}")
    
    # Navigation logic: School B (Control) cannot see the Tutor
    menu = ["📚 Digital Library", "🤖 Socratic Tutor", "📊 My Progress"]
    if user_school == "School B":
        menu = ["📚 Digital Library", "📊 My Progress"]
        
    choice = st.sidebar.radio("Research Navigation", menu)

    if choice == "📚 Digital Library":
        render_learning_path(user_school, user_role)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        render_progress(user_id)

def render_learning_path(school, role):
    st.subheader(f"📖 Chemistry Modules - {school}")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        # Filter content for the specific school
        my_data = df[df['Group'] == school]

        if not my_data.empty:
            for idx, row in my_data.iterrows():
                with st.expander(f"🔹 {row.get('Sub_Title', 'Unnamed Module')}"):
                    st.write(f"**Objectives:** {row.get('Learning_Objectives', 'N/A')}")
                    
                    # Multimodal Assets
                    col_asset, col_vid = st.columns(2)
                    with col_asset:
                        if row.get('File_Links'):
                            st.link_button("📄 View Textbook Page (PDF/Image)", row['File_Links'])
                    with col_vid:
                        if row.get('Video_Links'):
                            st.link_button("🎥 Watch Instructional Video", row['Video_Links'])

                    st.markdown("---")
                    st.write("📝 **4-Tier Diagnostic Assessment**")
                    
                    # Tiered Form for PhD Data Collection
                    with st.form(key=f"tier_form_{idx}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            t1 = st.radio("Tier 1: Select your Answer", ["A", "B", "C", "D"], key=f"t1_{idx}")
                            t2 = st.select_slider("Tier 2: Confidence in Answer", ["Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                        with c2:
                            t3 = st.text_area("Tier 3: Scientific Reason", key=f"t3_{idx}", placeholder="Explain why...")
                            t4 = st.select_slider("Tier 4: Confidence in Reason", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                        
                        if st.form_submit_button("Submit Assessment"):
                            # Logic to log into the standardized 'Assessment_Logs'
                            success = log_assessment(
                                user_id=st.session_state.user.get('User_ID'),
                                group=school,
                                module_id=row['Sub_Title'],
                                t1=t1, t2=t2, t3=t3, t4=t4,
                                diag="Pending Analysis",
                                misc="In Progress"
                            )
                            
                            if success:
                                # Prepare AI Session State
                                st.session_state.current_sub = row['Sub_Title']
                                st.session_state.current_tree = row.get('Socratic_Tree', "")
                                st.session_state.last_justification = t3
                                st.success("✅ Assessment Logged. " + ("Proceed to AI Tutor." if school == "School A" else ""))
                                log_temporal_trace(st.session_state.user.get('User_ID'), "SUBMIT_QUIZ", row['Sub_Title'])
        else:
            st.warning("No curriculum modules are currently live for your school.")
    except Exception as e:
        st.error(f"Module Load Error: {e}")

# --- AI CORE CONFIGURATION ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            system_instruction=SOCRATIC_PROMPT
        )
except Exception as e:
    st.error(f"AI Engine Error: {e}")

def render_socratic_tutor():
    st.subheader("🤖 Socratic Reasoning Assistant (Exp. Group Only)")

    if 'last_justification' not in st.session_state:
        st.info("💡 Please complete the assessment in 'Digital Library' first.")
        return

    concept = st.session_state.get('current_sub', "Chemistry")
    tree_logic = st.session_state.get('current_tree', "Guide the student through basic principles.")
    student_thought = st.session_state.get('last_justification', "")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"I've reviewed your reasoning on **{concept}**. You mentioned: *'{student_thought}'*. Let's explore that. What happens at the atomic level to cause this?"
        })

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Continue the discussion..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Injected Research Context
        research_context = (
            f"Topic: {concept}. Teacher's Socratic Logic: {tree_logic}. "
            f"Student said: {prompt}. Apply Socratic Method to fix misconceptions."
        )

        try:
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]
            ])
            response = chat.send_message(research_context)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            log_temporal_trace(st.session_state.user.get('User_ID'), "AI_CHAT", concept)
            
        except Exception as e:
            st.error(f"Tutoring Connection Error: {e}")

def render_progress(uid):
    st.subheader("📊 Your Research Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'] == uid]
        
        if not user_df.empty:
            # Show only relevant research tiers to the student
            display_cols = ['Timestamp', 'Module_ID', 'Tier_1', 'Tier_2', 'Tier_3', 'Tier_4']
            st.dataframe(user_df[display_cols], use_container_width=True)
        else:
            st.info("No assessments logged yet.")
    except:
        st.error("Progress data currently unavailable.")
