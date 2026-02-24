import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client, save_assignment

def show():
    user = st.session_state.user
    st.title("🧑‍🏫 Research Orchestration & Analytics")
    tab1, tab2, tab3 = st.tabs(["🚀 Deploy Module", "📊 Student Analytics", "📑 Assignments"])

    with tab1:
        st.subheader("Create New Socratic Module")
        with st.form("full_deploy_form"):
            col1, col2 = st.columns(2)
            main_t = col1.text_input("Chapter Name")
            sub_t = col2.text_input("Specific Concept")
            group = st.selectbox("Assign To", ["School A", "School B"])
            tree = st.text_area("Socratic Logic (Rules for Saathi AI)")
            
            st.markdown("---")
            q_text = st.text_area("Diagnostic Question")
            c1, c2 = st.columns(2)
            oa, ob, oc, od = c1.text_input("Opt A"), c2.text_input("Opt B"), c1.text_input("Opt C"), c2.text_input("Opt D")
            correct = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
            
            up_files = st.file_uploader("Upload PDF/Images", accept_multiple_files=True)
            
            if st.form_submit_button("Deploy to Students"):
                links = [upload_to_drive(f) for f in up_files] if up_files else []
                data = {
                    "sub_title": sub_t, "objectives": "Research Module", "file_link": ", ".join(links),
                    "video_link": "", "q_text": q_text, "oa": oa, "ob": ob, "oc": oc, "od": od,
                    "correct": correct, "socratic_tree": tree
                }
                if save_bulk_concepts(user['User_ID'], group, main_t, data):
                    st.success("Module deployed successfully!")

    with tab2:
        st.header("Metacognitive Distributions")
        try:
            client = get_gspread_client()
            df = pd.DataFrame(client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60").worksheet("Assessment_Logs").get_all_records())
            if not df.empty:
                st.plotly_chart(px.histogram(df, x="Tier_2 (Confidence_Ans)", color="Group", title="Class Confidence Distribution"))
            else:
                st.info("No student data yet.")
        except: st.error("Could not load logs.")
