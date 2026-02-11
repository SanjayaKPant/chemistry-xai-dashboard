import streamlit as st
import pandas as pd
from database_manager import get_gspread_client, log_student_response, log_temporal_trace

def show():
    user = st.session_state.user
    user_group = user.get('group', 'Control')
    
    st.title(f"🎓 Learning Portal: {user_group} Group")
    
    # Navigation
    if user_group == "Exp_A":
        st.sidebar.warning("🛡️ AI-Enabled Mode Active")
        menu = ["📚 Science Modules", "🤖 Socratic Tutor", "📊 My Progress"]
    else:
        st.sidebar.info("📘 Standard Mode Active")
        menu = ["📚 Digital Library", "📊 My Progress"]
        
    choice = st.sidebar.radio("Navigation", menu)

    if choice in ["📚 Science Modules", "📚 Digital Library"]:
        render_learning_path(user_group)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "📊 My Progress":
        render_progress(user['id'])

def render_learning_path(group):
    st.header("📂 Available Concepts")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        
        # Standardize headers
        df.columns = [c.strip().replace(' ', '_') for c in df.columns]
        my_data = df[df['Group'] == group]

        if not my_data.empty:
            for idx, row in my_data.iterrows():
                # UNIQUE KEY FIX: Adding 'idx' to the key ensures no duplicates
                with st.expander(f"🔹 CONCEPT: {row['Sub_Title']}"):
                    st.write(f"**Objective:** {row['Learning_Objectives']}")
                    
                    if row.get('Video_Links'):
                        v_links = str(row['Video_Links']).split('\n')
                        for link in v_links:
                            if "http" in link: st.video(link.strip())

                    st.markdown("---")
                    st.subheader("✍️ 4-Tier Diagnostic Check")
                    st.info(row.get('Four_Tier_Data', "No question data."))
                    
                    # Form with unique key
                    with st.form(key=f"quiz_form_{idx}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            t1 = st.radio("Tier 1: Answer", ["Option A", "Option B", "Option C"], key=f"t1_{idx}")
                            t2 = st.select_slider("Tier 2: Confidence", ["Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                        with col2:
                            t3 = st.text_area("Tier 3: Reasoning", key=f"t3_{idx}")
                            t4 = st.select_slider("Tier 4: Reasoning Confidence", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                        
                        if st.form_submit_button("Submit Response"):
                            log_student_response(st.session_state.user['id'], row['Sub_Title'], group, t1, t2, t3, t4)
                            log_temporal_trace(st.session_state.user['id'], "ASSESSMENT_SUBMIT", row['Sub_Title'])
                            
                            if group == "Exp_A":
                                # Pass the tree logic to the tutor
                                st.session_state.current_pivot = row.get('Socratic_Tree', "")
                                st.success("Response logged! Navigate to 'Socratic Tutor' to discuss.")
                            else:
                                st.success("Response logged!")
        else:
            st.warning("No modules deployed for your group yet.")
    except Exception as e:
        st.error(f"Error loading modules: {e}")

def render_socratic_tutor():
    st.header("🤖 Socratic Tutor")
    # Get pivot logic from session (set when student clicks 'Submit' or a module)
    pivot_logic = st.session_state.get('current_pivot', "")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I've reviewed your response. What's your current thinking on the Arrhenius definition?"}]

    for m in st.session_state.messages:
        st.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # --- SOCRATIC LOGIC ENGINE ---
        response = "That's an interesting point. Can you explain how that relates to the ions released in water?"
        
        if "|" in pivot_logic:
            try:
                # Format: IF: misconception | THEN: pivot_question
                parts = pivot_logic.split("|")
                if_part = parts[0].replace("IF:", "").strip().lower()
                then_part = parts[1].replace("THEN:", "").strip()
                
                if if_part in prompt.lower():
                    response = then_part
            except:
                pass 

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

def render_progress(user_id):
    st.header("📊 My Progress")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        # Filter for current user
        user_data = df[df['User_ID'] == user_id]
        
        if not user_data.empty:
            st.write(f"You have completed **{len(user_data)}** diagnostic checks.")
            # Simple summary table
            st.table(user_data[['Timestamp', 't1', 't3']])
        else:
            st.info("No assessment data found yet. Complete a module to see your progress!")
    except:
        st.error("Could not load progress data.")
