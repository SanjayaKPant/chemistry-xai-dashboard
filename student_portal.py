import streamlit as st
import pandas as pd
import google.generativeai as genai
from database_manager import get_gspread_client, log_student_response, log_temporal_trace

# --- ADVANCED SOCRATIC SYSTEM PROMPT (For High-Impact Research) ---
SOCRATIC_PROMPT = """
You are a Socratic Chemistry Tutor designed for PhD-level educational research. 
Your goal is to guide students toward conceptual clarity without ever giving the direct answer.

SCIENTIFIC APPROACH:
1. Identify Misconceptions: If a student provides a wrong explanation, do not say "You are wrong." Instead, ask a question that highlights the logical inconsistency (e.g., "If the pressure increases, what must happen to the volume according to Boyle’s Law?").
2. Sub-Microscopic Focus: Ground your questions in molecular behavior, ions, and energy changes.
3. Scaffolding: Provide hints in the form of thought experiments.

ETHICAL GUIDELINES:
1. Academic Integrity: Never solve equations for the student.
2. Encouragement: Acknowledge the complexity of Chemistry to reduce student anxiety.
"""

def show():
    # Defensive check to prevent KeyError if session state isn't fully loaded
    if 'user' not in st.session_state:
        st.error("Please log in again.")
        return

    user = st.session_state.user
    user_group = user.get('Group', 'Control') # Match the column name in your Sheet
    
    # sidebar info
    st.sidebar.title(f"👤 {user.get('Name', 'Researcher')}")
    st.sidebar.info(f"Group: {user_group}")
    
    menu = ["📚 Science Modules", "🤖 Socratic Tutor", "📊 My Progress"]
    if user_group == "Control":
        menu = ["📚 Digital Library", "📊 My Progress"]
        
    choice = st.sidebar.radio("Navigation", menu)

    if choice in ["📚 Science Modules", "📚 Digital Library"]:
        render_learning_path(user_group)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        # Fixed the 'id' key to match Google Sheet header 'User_ID'
        render_progress(user.get('User_ID'))

def render_learning_path(group):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        # Filtering by the group assigned in the Teacher Portal
        my_data = df[df['Group'] == group]

        if not my_data.empty:
            for idx, row in my_data.iterrows():
                with st.expander(f"🔹 {row.get('Sub_Title', 'Unnamed Module')}"):
                    st.write(f"**Objective:** {row.get('Learning_Objectives', 'N/A')}")
                    
                    if row.get('Video_Links'):
                        for link in str(row['Video_Links']).split('\n'):
                            if "http" in link: st.video(link.strip())

                    st.markdown("---")
                    st.info(f"**Diagnostic Question:**\n\n{row.get('Four_Tier_Data', 'No question data.')}")
                    
                    with st.form(key=f"form_v1_{idx}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            t1 = st.radio("Answer Choice", ["A", "B", "C", "D"], key=f"t1_{idx}")
                            t2 = st.select_slider("Confidence (Tier 2)", ["Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                        with c2:
                            t3 = st.text_area("Justification (Tier 3)", key=f"t3_{idx}", placeholder="Explain the molecular process...")
                            t4 = st.select_slider("Confidence (Tier 4)", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                        
                        if st.form_submit_button("Submit Response"):
                            user_id = st.session_state.user.get('User_ID')
                            log_student_response(user_id, row['Sub_Title'], group, t1, t2, t3, t4)
                            
                            # State management for AI
                            st.session_state.current_pivot = row.get('Socratic_Tree', "Ask about molecular collisions.")
                            st.session_state.current_sub = row['Sub_Title']
                            st.session_state.last_justification = t3
                            
                            if "messages" in st.session_state:
                                del st.session_state.messages
                                
                            st.success("✅ Saved! Go to 'Socratic Tutor' to discuss your answer.")
        else:
            st.warning("No lessons assigned to your group.")
    except Exception as e:
        st.error(f"Database Error: {e}")

# --- AI CONFIGURATION ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SOCRATIC_PROMPT
        )
    else:
        st.error("Gemini API Key missing in Secrets.")
except Exception as e:
    st.error(f"AI Setup Error: {e}")

def render_socratic_tutor():
    st.subheader("🤖 Socratic Reasoning Assistant")

    if 'last_justification' not in st.session_state:
        st.info("Please complete a Diagnostic Question in 'Science Modules' first.")
        return

    concept = st.session_state.get('current_sub', "Chemistry")
    pivot_logic = st.session_state.get('current_pivot', "Standard scaffolding")
    justification = st.session_state.get('last_justification', "")

    if st.button("🗑️ Clear Chat"):
        if "messages" in st.session_state:
            del st.session_state.messages
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"I've analyzed your thoughts on **{concept}**. You mentioned: *'{justification}'*. "
                       "Thinking about the sub-microscopic level, what evidence supports that thought?"
        })

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        context_prompt = (
            f"Subject: {concept}. Teacher's Pivot: {pivot_logic}. "
            f"Student said: {prompt}. Guide them Socratically."
        )

        try:
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]
            ])
            response = chat.send_message(context_prompt)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            log_temporal_trace(st.session_state.user.get('User_ID'), "AI_CHAT", f"Topic: {concept}")
            
        except Exception as e:
            st.error(f"AI Connection Error: {e}")

def render_progress(uid):
    st.subheader("📈 Your Research Journey")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        # Filter by the correct column 'User_ID'
        user_df = df[df['User_ID'] == uid]
        if not user_df.empty:
            st.dataframe(user_df, use_container_width=True)
        else:
            st.info("No logs found for your ID yet.")
    except Exception as e:
        st.error(f"Progress log error: {e}")
