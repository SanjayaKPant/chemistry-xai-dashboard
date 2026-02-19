import streamlit as st
import pandas as pd
import google.generativeai as genai
from database_manager import get_gspread_client, log_student_response, log_temporal_trace

def show():
    user = st.session_state.user
    user_group = user.get('group', 'Control')
    
    # Use .get() with a default to prevent crashes if 'name' is missing
    st.sidebar.title(f"👤 {user.get('name', 'Researcher')}")
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
        render_progress(user['id'])

def render_learning_path(group):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        df.columns = [c.strip().replace(' ', '_') for c in df.columns]
        my_data = df[df['Group'] == group]

        if not my_data.empty:
            for idx, row in my_data.iterrows():
                with st.expander(f"🔹 {row['Sub_Title']}"):
                    st.write(f"**Objective:** {row['Learning_Objectives']}")
                    
                    if row.get('Video_Links'):
                        for link in str(row['Video_Links']).split('\n'):
                            if "http" in link: st.video(link.strip())

                    st.markdown("---")
                    st.info(f"**Diagnostic Question:**\n\n{row.get('Four_Tier_Data')}")
                    
                    with st.form(key=f"form_v1_{idx}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            t1 = st.radio("Answer Choice", ["A", "B", "C", "D"], key=f"t1_{idx}")
                            t2 = st.select_slider("Confidence (Tier 2)", ["Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                        with c2:
                            t3 = st.text_area("Justification (Tier 3)", key=f"t3_{idx}", placeholder="Explain the molecular process...")
                            t4 = st.select_slider("Confidence (Tier 4)", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                        
                        if st.form_submit_button("Submit Response"):
                            log_student_response(st.session_state.user['id'], row['Sub_Title'], group, t1, t2, t3, t4)
                            
                            # --- CRITICAL FIX: Save these to session state for the AI ---
                            st.session_state.current_pivot = row.get('Socratic_Tree', "")
                            st.session_state.current_sub = row['Sub_Title']
                            st.session_state.last_justification = t3 # Added this
                            
                            # Clear old chat history when a new concept is submitted
                            if "messages" in st.session_state:
                                del st.session_state.messages
                                
                            st.success("✅ Saved! Go to 'Socratic Tutor' to discuss your answer.")
        else:
            st.warning("No lessons assigned to your group.")
    except Exception as e:
        st.error(f"Error: {e}")

# --- AI CONFIGURATION ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=(
            "You are a Socratic Chemistry Tutor for Nepali high school students. "
            "Focus on the sub-microscopic level (ions, molecules, and lattice structures). "
            "NEVER provide the correct answer. Instead, ask probing questions that lead "
            "the student to identify their own misconceptions in their Tier 3 justification."
        )
    )
except Exception as e:
    st.error("Gemini API Key missing or invalid in Secrets.")

def render_socratic_tutor():
    st.subheader("🤖 Socratic Reasoning Assistant")

    # 1. Verification: Ensure student has answered a question first
    if 'last_justification' not in st.session_state:
        st.info("Please complete a Diagnostic Question in 'Science Modules' first to start the AI session.")
        return

    concept = st.session_state.get('current_sub', "General Chemistry")
    pivot_logic = st.session_state.get('current_pivot', "Standard Socratic guidance")
    justification = st.session_state.get('last_justification', "")

    # Reset Chat Button (Essential for PhD Data Cleanliness)
    if st.button("🗑️ Clear Chat / Switch Topic"):
        if "messages" in st.session_state:
            del st.session_state.messages
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Initial AI prompt uses the actual student's justification
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"I've analyzed your thoughts on **{concept}**. You wrote: *'{justification}'*. "
                       "Thinking about the ions or molecules involved, what do you think happens when they collide?"
        })

    # Display chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Context-aware prompt
        context_prompt = (
            f"Context: Student is learning {concept}. "
            f"Teacher's Guided Pivot: {pivot_logic}. "
            f"Student's latest thought: {prompt}. "
            f"Use the Socratic method to challenge their logic."
        )

        try:
            # Multi-turn chat
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]
            ])
            response = chat.send_message(context_prompt)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Log for PhD analysis
            log_temporal_trace(st.session_state.user['id'], "AI_CHAT", f"Concept: {concept} | User: {prompt[:30]}")
            
        except Exception as e:
            st.error(f"AI Connection Error: {e}")

def render_progress(uid):
    st.subheader("📈 Your Research Journey")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'] == uid]
        if not user_df.empty:
            st.dataframe(user_df[['Timestamp', 'sub_title', 't1', 't3']], use_container_width=True)
        else:
            st.info("Complete your first assessment to see data here!")
    except:
        st.error("Progress log unreachable.")
