import streamlit as st
from database_manager import upload_and_log_material, log_temporal_trace

def show_teacher_portal(user):
    st.title(f"👨‍🏫 Teacher Command Center")
    st.subheader(f"User: {user['name']}") #
    
    # Sidebar for targeting specific experimental groups
    st.sidebar.header("Targeting")
    selected_group = st.sidebar.selectbox("Target Class Group", ["Exp_A", "Exp_B", "Control"])
    
    st.markdown("### 📚 Instructional Material Design")
    st.write("Upload materials to personalize the learning path for your students.")

    with st.form("teacher_upload_form", clear_on_submit=True):
        title = st.text_input("Lesson Title (e.g., The Bohr Model)")
        mode = st.radio("Instructional Track", ["Traditional (Control)", "AI-Integrated (Experimental)"])
        
        # Direct PDF Upload
        pdf_file = st.file_uploader("Upload Instructional PDF", type=['pdf'])
        
        desc = st.text_area("Detailed Learning Objectives / Task Instructions")
        
        # High Refinement AI Hint for personalized feedback
        ai_hint = ""
        if mode == "AI-Integrated (Experimental)":
            ai_hint = st.text_input("AI Scaffolding Hint (e.g., 'Target misconceptions about electron shells')")

        submit = st.form_submit_button("🚀 Publish & Systematize")

        if submit:
            if title and pdf_file:
                with st.spinner("Processing file and updating research database..."):
                    success = upload_and_log_material(
                        user['id'], 
                        selected_group, 
                        title, 
                        mode, 
                        pdf_file, 
                        desc, 
                        ai_hint
                    )
                    
                    if success:
                        log_temporal_trace(user['id'], f"Published {title} to {selected_group}")
                        st.success(f"✅ Lesson '{title}' is now live for group {selected_group}!")
                    else:
                        st.error("Failed to publish. Check tab names in Google Sheets.")
            else:
                st.error("Please provide both a Lesson Title and a PDF file.")

    st.divider()
    st.header("📊 Recent Activity")
    st.info(f"Systematic folder organization is active. All files are being logged for the {selected_group} cohort.")
