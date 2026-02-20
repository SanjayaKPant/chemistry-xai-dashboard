import streamlit as st
from database_manager import save_bulk_concepts, upload_to_drive

def show():
    user = st.session_state.user
    st.title("🧑‍🏫 Teacher Orchestration Dashboard")
    
    with st.form("lesson_form"):
        col1, col2 = st.columns(2)
        with col1:
            main_title = st.text_input("Chapter Title", "Classification of Elements")
            target_group = st.selectbox("Assign to Group", ["School A", "School B"])
        with col2:
            sub_title = st.text_input("Specific Concept", "Modern Periodic Law")
            objectives = st.text_area("Learning Objectives")

        st.markdown("---")
        up_file = st.file_uploader("Upload Textbook Page (PDF/Image)", type=['pdf', 'png', 'jpg'])
        vid_link = st.text_input("Video URL (YouTube/Web)")
        socratic_logic = st.text_area("Socratic Scaffolding Logic (For School A Gemini)")

        if st.form_submit_button("🚀 Deploy Module"):
            with st.spinner("Syncing to Sheets..."):
                file_url = upload_to_drive(up_file) if up_file else ""
                c_data = {
                    "sub_title": sub_title,
                    "objectives": objectives,
                    "file_link": file_url,
                    "video_link": vid_link,
                    "socratic_tree": socratic_logic
                }
                if save_bulk_concepts(user['User_ID'], target_group, main_title, c_data):
                    st.success(f"Deployed for {target_group}!")
                    st.cache_data.clear()
