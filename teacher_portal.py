import streamlit as st
import pandas as pd
from database_manager import upload_and_log_material, get_gspread_client

def show():
    # --- LMS STYLE TOP BAR ---
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("---")

    # Persistent Navigation Toolbar
    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Class Analytics", "🧩 Misconception Tracker", "📂 Material Audit"])

    with tabs[0]:
        render_deployment_zone()

    with tabs[1]:
        render_class_analytics()

    with tabs[2]:
        render_misconception_tracker()
        
    with tabs[3]:
        render_audit_logs()

def render_deployment_zone():
    st.subheader("Publish New Instructional Module")
    # This section uses the "Batching" logic we discussed (st.form)
    with st.form("deployment_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Module Name", placeholder="e.g., VSEPR Theory")
            group = st.selectbox("Assign to Group", ["Control", "Exp_A", "Both"])
            mode = st.selectbox("Instructional Mode", ["Traditional", "AI-Scaffolded (XAI)"])
        
        with col2:
            uploaded_file = st.file_uploader("Upload Lesson PDF", type=['pdf'])
            desc = st.text_area("Learning Objective (For AI Context)")

        hint = st.text_area("Custom AI Scaffold Hint", help="This hint will be displayed as an expander for Group A.")

        if st.form_submit_button("Deploy to Student Portals"):
            if uploaded_file and title:
                success = upload_and_log_material(
                    st.session_state.user['id'], group, title, mode, uploaded_file, desc, hint
                )
                if success:
                    st.success(f"Successfully deployed '{title}'!")
                    st.balloons()
            else:
                st.warning("Please provide a title and a file.")

def render_class_analytics():
    st.subheader("📈 Real-time Student Engagement")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Load the logs we created earlier
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        
        if not traces.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Activity by Event Type**")
                st.bar_chart(traces['Event'].value_counts())
            with col2:
                st.write("**Top Active Students**")
                st.dataframe(traces['User_ID'].value_counts(), use_container_width=True)
        else:
            st.info("No student activity recorded yet.")
    except:
        st.write("Awaiting data...")

def render_misconception_tracker():
    st.subheader("🧩 Conceptual Change Monitor")
    st.markdown("Identifying gaps in student understanding using **Assessment_Logs**.")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            # Highlighting misconceptions for the teacher
            misconceptions = logs[logs['Misconception'] != "None"]
            st.warning(f"Alert: {len(misconceptions)} misconceptions detected in current modules.")
            st.dataframe(misconceptions[['User_ID', 'Module_ID', 'Misconception']], use_container_width=True)
            
            # Professional Market Visualization
            st.write("**Misconception Frequency**")
            st.bar_chart(misconceptions['Misconception'].value_counts())
        else:
            st.info("No assessments completed yet.")
    except:
        st.error("Could not load Assessment_Logs. Ensure the sheet exists.")

def render_audit_logs():
    st.subheader("📂 Published Materials Library")
    # Allows teacher to delete or view previously sent materials
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
    st.dataframe(mats, use_container_width=True)
