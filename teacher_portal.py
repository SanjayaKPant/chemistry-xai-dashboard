import streamlit as st
from database_manager import upload_and_log_material, get_gspread_client
import pandas as pd

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("### Deploy Instructional Modules & AI Scaffolding")

    # 1. User Context: The app needs to know WHO is uploading
    teacher_id = st.session_state.user['id']

    # 2. The Input Form: Grouped for clarity
    with st.form("teacher_upload_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Module Title", placeholder="e.g., Atomic Structure")
            group = st.selectbox("Target Student Group", ["Control", "Exp_A", "Both"])
            mode = st.selectbox("Instructional Mode", ["Traditional", "AI-Scaffolded"])
        
        with col2:
            # The File Uploader: This handles the actual PDF
            uploaded_file = st.file_uploader("Upload Chemistry PDF", type=['pdf'])
            description = st.text_area("Learning Objectives", placeholder="What should students learn?")

        # Plan B Variable: The AI Scaffold
        hint = st.text_area("AI-Generated Hint (Optional)", help="Only visible to Experimental Group A")

        submit_button = st.form_submit_button("🚀 Deploy to Shared Research Drive")

        # 3. The Logic Bridge: Connecting to Database Manager
        if submit_button:
            if uploaded_file and title:
                # We call the function you just double-checked!
                success = upload_and_log_material(
                    teacher_id=teacher_id,
                    group=group,
                    title=title,
                    mode=mode,
                    file_obj=uploaded_file,
                    desc=description,
                    hint=hint
                )
                
                if success:
                    st.success(f"Successfully published '{title}'! Data logged for research.")
                    st.balloons()
                else:
                    st.error("Deployment failed. Check the logs in database_manager.")
            else:
                st.warning("Please provide both a Title and a PDF file.")

    # 4. Horizontal Progress: Live Audit for the Teacher
    st.divider()
    st.subheader("Current Published Materials")
    # This helps the teacher verify that the "Bridge" to Google Sheets is working
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        if not mats.empty:
            st.dataframe(mats, use_container_width=True)
    except:
        st.info("Awaiting first deployment...")
