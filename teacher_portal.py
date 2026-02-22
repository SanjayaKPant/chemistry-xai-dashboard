import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client, save_assignment

def show():
    user = st.session_state.user
    st.title("🧑‍🏫 LMS Orchestration & Research Hub")
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Deployment", "📊 Analytics", "📈 Engagement", "📑 Assignments"])

    with tab1:
        st.subheader("Module Deployment")
        with st.form("deploy_form"):
            c1, c2 = st.columns(2)
            main_t = c1.text_input("Chapter")
            sub_t = c2.text_input("Concept")
            group = st.selectbox("Group", ["School A", "School B"])
            
            # MULTIPLE FILE UPLOADER
            up_files = st.file_uploader("Upload Resources", accept_multiple_files=True)
            
            if st.form_submit_button("Deploy Module"):
                links = [upload_to_drive(f) for f in up_files] if up_files else []
                file_string = ", ".join(links) # Combine links into one cell
                
                data = {"sub_title": sub_t, "file_link": file_string} 
                if save_bulk_concepts(user['User_ID'], group, main_t, data):
                    st.success("Module Live!")

    with tab2:
        st.header("Learning Analytics")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
            if not df.empty:
                st.plotly_chart(px.histogram(df, x="Tier_2", title="Confidence Distribution"))
                st.dataframe(df)
            else: st.info("No assessment data yet.")
        except: st.error("Assessment sheet inaccessible.")

    with tab3:
        st.header("Engagement")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            if not df.empty:
                st.plotly_chart(px.pie(df, names="Event"))
            else: st.info("No engagement data found.")
        except: st.error("Traces sheet inaccessible.")

    with tab4:
        st.subheader("Post Assignment")
        with st.form("assign_form"):
            a_title = st.text_input("Task Title")
            a_group = st.selectbox("Assign To", ["School A", "School B"], key="a_t")
            a_desc = st.text_area("Instructions")
            a_file = st.file_uploader("Assignment Material")
            if st.form_submit_button("Push to Student Portal"):
                f_url = upload_to_drive(a_file) if a_file else ""
                if save_assignment(user['User_ID'], a_group, a_title, a_desc, f_url):
                    st.success("Assignment live!")
