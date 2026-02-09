import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("---")

    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Class Analytics", "🧩 Misconception Tracker", "📂 Material Audit"])

    with tabs[0]:
        render_deploy_lessons()

    with tabs[1]:
        render_class_analytics()

    with tabs[2]:
        render_misconception_tracker()

    with tabs[3]:
        render_audit_logs()

def render_deploy_lessons():
    st.subheader("🚀 Dual-Path Lesson Deployment")
    st.info("Upload different materials for each group to isolate the AI variable.")
    
    with st.form("advanced_deploy", clear_on_submit=True):
        mod_id = st.text_input("Module ID (e.g., CHEM_ACID_01)", placeholder="Unique ID for this lesson")
        topic = st.text_input("Lesson Topic", placeholder="e.g., Properties of Bases")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📘 Control Group Path")
            st.caption("Standard Digital Access (No AI)")
            c_files = st.file_uploader("Upload PDFs/Images (Control)", accept_multiple_files=True, key="c_upload")
            c_video = st.text_input("Video URL (Control)", placeholder="YouTube/Vimeo link")
            
        with col2:
            st.markdown("### 🧪 Experimental Group Path")
            st.caption("AI-Scaffolded (Socratic Tutor enabled)")
            e_files = st.file_uploader("Upload PDFs/Images (Experimental)", accept_multiple_files=True, key="e_upload")
            e_video = st.text_input("Video URL (Experimental)", placeholder="YouTube/Vimeo link")
            
            # THE RESEARCH ANCHOR
            socratic_anchor = st.text_area("Socratic Pivot/Anchor", 
                placeholder="What specific question should the AI ask to challenge the misconception?")

        st.markdown("---")
        submit = st.form_submit_button("Deploy Dual-Path Lesson")
        
        if submit:
            if mod_id and topic:
                save_dual_deployment(mod_id, topic, c_video, e_video, socratic_anchor)
                st.success(f"Successfully deployed '{topic}' to both research paths.")
            else:
                st.warning("Please provide at least a Module ID and Topic.")

def render_class_analytics():
    st.subheader("📊 Comparative Engagement Metrics")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            c1, c2 = st.columns(2)
            c1.metric("Total Submissions", len(logs))
            c2.metric("Unique Students", logs['User_ID'].nunique())
            
            st.write("### Participation: Exp_A vs Control")
            st.bar_chart(logs['Group'].value_counts())
        else:
            st.info("Awaiting data from student participants...")
    except Exception as e:
        st.error(f"Analytics Error: {e}")

def render_misconception_tracker():
    st.subheader("🧩 Conceptual Change Engine")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if not logs.empty:
            st.write("### High-Confidence Misconceptions (Critical Flags)")
            # Flagging Wrong Answer + High Confidence
            critical = logs[(logs['Diagnostic_Result'] == 'Misconception')]
            st.dataframe(critical[['User_ID', 'Tier_1 (Answer)', 'Tier_3 (Reason)', 'Group']])
        else:
            st.info("No diagnostic data available yet.")
    except Exception as e:
        st.error(f"Tracker Error: {e}")

def render_audit_logs():
    st.subheader("📂 Instructional Material Audit")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats, use_container_width=True)
    except:
        st.warning("No deployment records found.")

def save_dual_deployment(mod_id, topic, c_vid, e_vid, anchor):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        # Logging the deployment parameters for research verification
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            mod_id,
            topic,
            c_vid,
            e_vid,
            anchor
        ])
    except Exception as e:
        st.error(f"Deployment Save Error: {e}")
