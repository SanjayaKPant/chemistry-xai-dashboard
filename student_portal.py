import streamlit as st
import pandas as pd
from database_manager import get_gspread_client, log_student_response, log_temporal_trace

def show():
    user = st.session_state.user
    user_group = user.get('group', 'Control')
    
    st.sidebar.title(f"👤 {user.get('name')}")
    st.sidebar.info(f"Group: {user_group}")
    
    menu = ["📚 Science Modules", "🤖 Socratic Tutor", "📊 My Progress"]
    if user_group == "Control":
        menu = ["📚 Digital Library", "📊 My Progress"] # No AI for control
        
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
                # FIX: Unique key using index + title
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
                            t3 = st.text_area("Justification (Tier 3)", key=f"t3_{idx}")
                            t4 = st.select_slider("Confidence (Tier 4)", ["Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")
                        
                        if st.form_submit_button("Submit Response"):
                            log_student_response(st.session_state.user['id'], row['Sub_Title'], group, t1, t2, t3, t4)
                            # Set the pivot for the AI tutor
                            st.session_state.current_pivot = row.get('Socratic_Tree', "")
                            st.session_state.current_sub = row['Sub_Title']
                            st.success("✅ Response Saved! You can now discuss this in the Socratic Tutor tab.")
        else:
            st.warning("No lessons assigned to your group.")
    except Exception as e:
        st.error(f"Error: {e}")

def render_socratic_tutor():
    st.subheader("🤖 Socratic Reasoning Assistant")
    pivot = st.session_state.get('current_pivot', "")
    target_concept = st.session_state.get('current_sub', "General Chemistry")

    if not pivot:
        st.warning("Please complete a diagnostic check in 'Science Modules' first to start a targeted discussion.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"I've analyzed your thoughts on {target_concept}. How did you arrive at that conclusion?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if prompt := st.chat_input("Type your explanation..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Socratic Logic Engine
        bot_res = "Can you elaborate on the chemical process occurring there?"
        if "|" in pivot:
            trigger, pivot_q = pivot.split("|")[0].lower(), pivot.split("|")[1]
            if any(word in prompt.lower() for word in trigger.replace("if:", "").strip().split()):
                bot_res = pivot_q.replace("THEN:", "").strip()
        
        st.session_state.messages.append({"role": "assistant", "content": bot_res})
        st.rerun()

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
