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
    st.subheader("Publish New Instructional Module")
    with st.form("deployment_form"):
        col1, col2 = st.columns(2)
        with col1:
            mod_name = st.text_input("Module Name", placeholder="e.g., Atomic Structure")
            group = st.selectbox("Assign to Group", ["Exp_A", "Control"])
        with col2:
            uploaded_file = st.file_uploader("Upload Lesson PDF", type="pdf")
            mode = st.selectbox("Instructional Mode", ["AI-Scaffolded", "Traditional"])
        
        submit = st.form_submit_button("Deploy to Student Portals")
        if submit and mod_name and uploaded_file:
            save_deployment(mod_name, group, mode)
            st.success(f"Deployed {mod_name} to {group}!")

def render_class_analytics():
    st.subheader("📊 Class Analytics & Engagement")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Submissions", len(logs))
            c2.metric("Active Students", logs['User_ID'].nunique())
            # Completion check based on Tier 4 presence
            completions = logs[logs['Tier_4 (Confidence_Reas)'].astype(str).str.strip() != ""].shape[0]
            c3.metric("Full 4-Tier Completions", completions)
            
            st.write("### Participation by Group")
            st.bar_chart(logs['Group'].value_counts())
    except Exception as e:
        st.error(f"Analytics Error: {e}")

def render_misconception_tracker():
    st.subheader("🧩 Detailed Misconception Analysis")
    st.info("This tool identifies patterns between student answers (Tier 1) and their reasoning (Tier 3).")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if not logs.empty:
            # 📊 1. Group-wise Diagnostic Visualization
            st.write("### 📈 Scientific Status Distribution")
            if 'Diagnostic_Result' in logs.columns:
                status_counts = logs['Diagnostic_Result'].value_counts()
                st.bar_chart(status_counts)
            
            # 🧩 2. High-Confidence Misconception Alert
            # A Misconception is often defined as Wrong Answer + High Confidence
            st.write("### ⚠️ Critical Misconception Flags")
            misconception_filter = (
                (logs['Diagnostic_Result'] == "Misconception") & 
                (logs['Tier_4 (Confidence_Reas)'].astype(str).str.contains("High|Sure|4|5"))
            )
            critical_list = logs[misconception_filter]
            
            if not critical_list.empty:
                st.warning(f"Detected {len(critical_list)} students with deep-seated misconceptions.")
                st.dataframe(critical_list[['User_ID', 'Module_ID', 'Tier_1 (Answer)', 'Tier_3 (Reason)', 'Misconception_Tag']])
            else:
                st.success("No high-confidence misconceptions detected currently.")

            # 📋 3. Full Research Data View
            with st.expander("🔍 View Full 4-Tier Assessment Logs"):
                st.dataframe(logs[['Timestamps', 'User_ID', 'Tier_1 (Answer)', 'Tier_3 (Reason)', 'Diagnostic_Result', 'Group']])
        else:
            st.info("Awaiting student data flow to Assessment_Logs...")

    except Exception as e:
        st.error(f"Tracker Error: {e}")

def render_audit_logs():
    st.subheader("📂 Material Audit")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats)
    except:
        st.warning("Audit logs are empty.")

def save_deployment(name, group, mode):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), name, group, mode])
    except Exception as e:
        st.error(f"Log Error: {e}")
