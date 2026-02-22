import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client, save_assignment

def show():
    user = st.session_state.user
    st.title("🧑‍🏫 LMS Orchestration & Research Hub")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Deployment", "📊 Analytics", "📈 Engagement", "📑 Assignments"])

    with tab1:
        st.subheader("Deploy Learning Module")
        with st.form("deploy_form"):
            c1, c2 = st.columns(2)
            main_t = c1.text_input("Chapter/Unit")
            sub_t = c2.text_input("Specific Concept")
            group = st.selectbox("Target Group", ["School A", "School B"])
            objectives = st.text_area("Learning Objectives")
            
            up_files = st.file_uploader("Upload Resources (Multiple PDFs/Images)", accept_multiple_files=True)
            vid_url = st.text_input("Video URL")
            
            st.markdown("---")
            st.write("4-Tier Assessment Setup")
            q_text = st.text_area("Diagnostic Question")
            oa = st.text_input("Option A")
            ob = st.text_input("Option B")
            oc = st.text_input("Option C")
            od = st.text_input("Option D")
            correct = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
            socratic_tree = st.text_area("Socratic Scaffolding Logic (For School A AI)")

            if st.form_submit_button("Deploy Module"):
                links = [upload_to_drive(f) for f in up_files] if up_files else []
                file_string = ", ".join(links)
                data = {
                    "sub_title": sub_t, "objectives": objectives, "file_link": file_string,
                    "video_link": vid_url, "q_text": q_text, "oa": oa, "ob": ob, 
                    "oc": oc, "od": od, "correct": correct, "socratic_tree": socratic_tree
                }
                if save_bulk_concepts(user['User_ID'], group, main_t, data):
                    st.success("Module Deployed successfully!")

    with tab2:
        st.header("Learning Analytics")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
            if not df.empty:
                st.plotly_chart(px.histogram(df, x="Tier_2", color="Group", title="Student Confidence by Group"))
                st.dataframe(df)
            else:
                st.info("No assessment data recorded yet.")
        except: st.error("Analytics sheet inaccessible.")

    with tab3:
        st.header("Engagement & Attendance")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            if not df.empty:
                st.plotly_chart(px.bar(df['Event'].value_counts().reset_index(), x='index', y='Event', title="Portal Activity"))
            else:
                st.info("No engagement traces found.")
        except: st.error("Engagement data error.")

    with tab4:
        st.subheader("Assignment Management")
        with st.form("assign_form"):
            a_title = st.text_input("Assignment Title")
            a_group = st.selectbox("Assign To", ["School A", "School B"], key="as_grp")
            a_desc = st.text_area("Instructions")
            a_file = st.file_uploader("Reference PDF")
            if st.form_submit_button("Deploy Assignment"):
                f_url = upload_to_drive(a_file) if a_file else ""
                if save_assignment(user['User_ID'], a_group, a_title, a_desc, f_url):
                    st.success("Assignment is now live!")
