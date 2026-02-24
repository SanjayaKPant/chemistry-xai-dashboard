import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client, save_assignment
from datetime import datetime

def show():
    if 'user' not in st.session_state:
        st.error("Please login first.")
        st.stop()
        
    user = st.session_state.user
    st.title("🧑‍🏫 Research Orchestration & Analytics")
    st.info(f"Researcher: {user.get('Name')} | ID: {user.get('User_ID')}")

    # Tabs for different research functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Deploy Socratic Module", 
        "📊 Student Analytics", 
        "📑 Assignments",
        "⚙️ Manage Content"
    ])

    # --- TAB 1: FULL MODULE DEPLOYMENT ---
    with tab1:
        st.subheader("Create New Socratic Learning Module")
        with st.form("full_deploy_form"):
            col1, col2 = st.columns(2)
            main_t = col1.text_input("Chapter Name (Main Title)", placeholder="e.g., Chemical Bonding")
            sub_t = col2.text_input("Specific Concept (Sub Title)", placeholder="e.g., Ionic Bonding")
            group = st.selectbox("Assign To Research Group", ["School A", "School B", "Control Group"])
            
            objectives = st.text_area("Learning Objectives (PhD Requirement)", 
                                     placeholder="Describe what the student should be able to explain...")
            
            st.markdown("---")
            st.subheader("📖 Pedagogical Materials")
            up_files = st.file_uploader("Upload Lesson Materials (PDF/Images)", accept_multiple_files=True)
            vid_url = st.text_input("Video Resource URL (YouTube/Google Drive Link)")
            
            st.markdown("---")
            st.subheader("🧪 Misconception Tracker (4-Tier Diagnostic)")
            tree = st.text_area("Socratic Logic (Rules for Saathi AI)", 
                               placeholder="If student says X, ask Y. The scientific truth is Z.")
            
            q_text = st.text_area("Diagnostic Question Text")
            
            c1, c2 = st.columns(2)
            oa = c1.text_input("Option A (Correct/Distractor)")
            ob = c2.text_input("Option B (Distractor)")
            oc = c1.text_input("Option C (Distractor)")
            od = c2.text_input("Option D (Distractor)")
            
            correct = st.selectbox("Correct Answer Key", ["A", "B", "C", "D"])
            
            submit = st.form_submit_button("🚀 Deploy to Student Portals")
            
            if submit:
                with st.spinner("Uploading materials and syncing database..."):
                    # 1. Handle File Uploads to Google Drive
                    links = []
                    if up_files:
                        for f in up_files:
                            link = upload_to_drive(f)
                            if link: links.append(link)
                    
                    # 2. Package Data for the 12-Column PhD Logger
                    data = {
                        "sub_title": sub_t,
                        "objectives": objectives,
                        "file_link": ", ".join(links),
                        "video_link": vid_url,
                        "q_text": q_text,
                        "oa": oa, "ob": ob, "oc": oc, "od": od,
                        "correct": correct,
                        "socratic_tree": tree
                    }
                    
                    # 3. Save to GSheets
                    success = save_bulk_concepts(user['User_ID'], group, main_t, data)
                    if success:
                        st.success(f"✅ Module '{sub_t}' deployed successfully with {len(links)} attachments!")
                        st.balloons()

    # --- TAB 2: RESEARCH ANALYTICS ---
    with tab2:
        st.header("Metacognitive Distributions")
        
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
            
            if not df.empty:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("### Confidence Levels by Group")
                    fig1 = px.histogram(df, x="Tier_2 (Confidence_Ans)", color="Group", barmode="group")
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col_b:
                    st.write("### Correctness vs. Confidence")
                    # Visualizing Calibration (PhD Critical Data)
                    fig2 = px.scatter(df, x="Tier_2 (Confidence_Ans)", y="Result", color="Group", hover_data=['User_ID'])
                    st.plotly_chart(fig2, use_container_width=True)
                
                st.write("### Raw Research Data")
                st.dataframe(df)
            else:
                st.info("Waiting for students to submit diagnostic data...")
        except Exception as e:
            st.error(f"Could not load analytics: {e}")

    # --- TAB 3: ASSIGNMENTS ---
    with tab3:
        st.subheader("Deploy Homework or Post-Tests")
        with st.form("assignment_form"):
            a_title = st.text_input("Assignment Title")
            a_desc = st.text_area("Instructions")
            a_group = st.selectbox("Target Group", ["School A", "School B"], key="assign_group")
            a_file = st.file_uploader("Upload Worksheet (Optional)", key="assign_file")
            
            if st.form_submit_button("Post Assignment"):
                file_url = upload_to_drive(a_file) if a_file else ""
                if save_assignment(user['User_ID'], a_group, a_title, a_desc, file_url):
                    st.success(f"Assignment '{a_title}' posted!")

    # --- TAB 4: CONTENT MANAGEMENT ---
    with tab4:
        st.subheader("Active Modules")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            m_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
            st.table(m_df[['Group', 'Main_Title', 'Sub_Title']])
        except:
            st.write("No modules found.")
