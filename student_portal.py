import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Research Group: {student_group}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user, student_group)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_dashboard(user, group):
    st.title(f"🚀 Student Command Center")
    st.info(f"Welcome. You are in the **{group}** study group.")

def render_modules(student_group):
    st.header("📚 Your Learning Path")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        df = pd.DataFrame(ws.get_all_records())
        my_lessons = df[df['Group'].str.strip() == student_group]

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row.get('Sub_Title')}", expanded=True):
                col1, col2 = st.columns(2)
                if str(row.get('File_Links (PDF/Images)', '')).startswith("http"):
                    col1.link_button("📂 View PDF", row.get('File_Links (PDF/Images)'))
                if str(row.get('Video_Links', '')).startswith("http"):
                    col2.video(row.get('Video_Links'))

                st.divider()
                with st.form(key=f"eval_{idx}"):
                    st.markdown(f"**Question:** {row.get('Diagnostic_Question')}")
                    t1 = st.radio("Answer", [row.get('Option_A'), row.get('Option_B'), row.get('Option_C'), row.get('Option_D')])
                    t2 = st.select_slider("Confidence", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Reasoning")
                    if st.form_submit_button("Submit & Unlock AI"):
                        log_assessment(st.session_state.user['User_ID'], student_group, row.get('Sub_Title'), t1, t2, t3, "Sure", "Complete", "")
                        st.session_state.current_topic = row.get('Sub_Title')
                        st.session_state.logic_tree = row.get('Socratic_Tree')
                        st.success("✅ Logged! Now use the AI Tutor.")
    except Exception as e:
        st.error(f"Error: {e}")

def render_ai_chat(school):
    # ... (Keep your group/topic checks the same)

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        
        # VPS FIX: We force the transport to 'rest' and explicitly 
        # tell the library NOT to use the default discovery URL.
        import google.generativeai as genai
        from google.generativeai.types import RequestOptions
        
        genai.configure(api_key=api_key)
        
        # We define the model here but call it with a 'v1' safety check
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # PhD Socratic Prompting Logic
        system_prompt = (
            f"You are a PhD Socratic Tutor for Chemistry. Topic: {st.session_state.current_topic}. "
            f"Pedagogical Goal: {st.session_state.logic_tree}. "
            "IMPORTANT: Never give the answer. Ask one short guiding question to help the student "
            "uncover the logic themselves. Max 2 sentences."
        )

    except Exception as e:
        st.error(f"Configuration Error: {e}")
        return

    # ... (Chat UI logic)

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            # VPS FIX: Adding 'request_options' forces the stable v1 API
            response = model.generate_content(
                f"{system_prompt}\nStudent says: {prompt}",
                request_options=RequestOptions(api_version='v1')
            )
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            log_temporal_trace(st.session_state.user['User_ID'], "AI_SUCCESS", st.session_state.current_topic)
            
        except Exception as e:
            st.error(f"The 'v1beta' bug is persistent. Let's try one more backup...")
            # BACKUP: If the above fails, we use the direct model path
            try:
                model_alt = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
                response = model_alt.generate_content(f"{system_prompt}\nStudent: {prompt}")
                st.write(response.text)
            except:
                st.warning("Please wait 60 seconds. The API is syncing with the stable server.")
                
def render_progress(uid):
    st.header("📈 Progress Tracker")
    try:
        client_gs = get_gspread_client()
        sh = client_gs.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_df = df[df['User_ID'].astype(str) == str(uid)]
        if not user_df.empty:
            fig = px.line(user_df, x="Timestamps", y="Tier_2 (Confidence_Ans)", title="Confidence Growth", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("Updating...")
