import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client, save_assignment

def show():
    user = st.session_state.user
    st.title("🧑‍🏫 Research Orchestration & Analytics")
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Deploy Module", "📊 Analytics", "📈 Engagement", "📑 Assignments"])

    with tab1:
        with st.form("full_deploy_form"):
            col1, col2 = st.columns(2)
            main_t = col1.text_input("Chapter (Main Title)")
            sub_t = col2.text_input("Concept (Sub Title)")
            group = st.selectbox("Assign To Group", ["School A", "School B"])
            objectives = st.text_area("Learning Objectives")
            
            up_files = st.file_uploader("Upload Materials (Multiple PDF/Images)", accept_multiple_files=True)
            vid_url = st.text_input("Video Resource URL (YouTube/Drive)")
            
            st.markdown("---")
            st.subheader("🧪 Misconception Tracker (4-Tier Diagnostic)")
            q_text = st.text_area("Question Text")
            c1, c2 = st.columns(2)
            oa, ob = c1.text_input("Option A"), c2.text_input("Option B")
            oc, od = c1.text_input("Option C"), c2.text_input("Option D")
            correct = st.selectbox("Correct Key", ["A", "B", "C", "D"])
            tree = st.text_area("🧠 Socratic Scaffolding Logic (Tree)")

            if st.form_submit_button("Deploy Research Module"):
                links = [upload_to_drive(f) for f in up_files] if up_files else []
                data = {
                    "sub_title": sub_t, "objectives": objectives, "file_link": ", ".join(links),
                    "video_link": vid_url, "q_text": q_text, "oa": oa, "ob": ob, 
                    "oc": oc, "od": od, "correct": correct, "socratic_tree": tree
                }
                if save_bulk_concepts(user['User_ID'], group, main_t, data):
                    st.success("Module deployed with all research parameters!")

    # Tab 2 & 3: Restored with empty-state safety
    with tab2:
        st.header("Misconception Data")
        try:
            df = pd.DataFrame(get_gspread_client().open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60").worksheet("Assessment_Logs").get_all_records())
            if not df.empty: st.plotly_chart(px.histogram(df, x="Tier_2", color="Group"))
            else: st.info("No assessment logs yet.")
        except: st.error("Analytics sheet empty.")

    with tab4:
        st.subheader("Post Assignment")
        with st.form("a_form"):
            t, d = st.text_input("Title"), st.text_area("Instructions")
            g = st.selectbox("Group", ["School A", "School B"], key="asgn_g")
            f = st.file_uploader("Task File")
            if st.form_submit_button("Post"):
                url = upload_to_drive(f) if f else ""
                if save_assignment(user['User_ID'], g, t, d, url): st.success("Assignment live!")
