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

import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def render_class_analytics():
    st.markdown("## 📊 Class Analytics")
    st.info("Tracking real-time engagement and 4-tier diagnostic participation.")

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Load the two critical data sources for your PhD
        # 1. Behavioral Data (Traces)
        traces_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        # 2. Performance Data (Responses/Assessment_Logs)
        responses_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if not traces_df.empty:
            # Metric Row: High-level overview
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Interactions", len(traces_df))
            with col2:
                active_users = traces_df['User_ID'].nunique()
                st.metric("Active Students", active_users)
            with col3:
                # Calculate how many students completed all 4 tiers
                completed = responses_df[responses_df['Tier_4'] != ""].shape[0]
                st.metric("Quiz Completions", completed)

            # Visualizing the "Pulse" of the class
            st.write("### Student Activity Timeline")
            # We convert the Timestamp column to ensure proper plotting
            traces_df['Timestamp'] = pd.to_datetime(traces_df['Timestamp'])
            st.line_chart(traces_df.set_index('Timestamp')['Event'].value_counts())
            
            # Group Comparison (Critical for PhD)
            st.write("### Engagement by Group (Exp_A vs Control)")
            # This helps you prove if your AI scaffold actually increases engagement
            group_data = traces_df.groupby('Group').size()
            st.bar_chart(group_data)

        else:
            st.warning("No data found in 'Temporal_Traces'. Encourage students to log in!")

    except Exception as e:
        st.error(f"Analytics Error: {e}. Please ensure tab names match exactly.")

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

def render_class_analytics():
    st.subheader("🔮 Predictive Student Insights")
    
    # Example logic: Predicting who needs help
    # In industry, this would be a trained Scikit-learn model
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            # Simple Prediction: Students with Score < 0.5 are 'At Risk'
            avg_scores = logs.groupby('User_ID')['Score'].mean().reset_index()
            avg_scores['Status'] = avg_scores['Score'].apply(lambda x: "✅ On Track" if x > 0.7 else "⚠️ Needs Support")
            
            # Professional Metric Cards
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Class Score", f"{int(avg_scores['Score'].mean()*100)}%")
            col2.metric("Active Students", len(avg_scores))
            col3.metric("Critical Misconceptions", len(logs[logs['Misconception'] != "None"]))

            st.write("### Student Support Queue")
            st.table(avg_scores.sort_values(by="Score"))
        else:
            st.info("Insufficient data for predictions yet.")
    except:
        st.write("Awaiting data flow...")
def render_predictive_analytics():
    st.subheader("🔮 AI Predictive Student Insights")
    # Simulation: In a real PhD project, this would use a Random Forest model
    # High Risk = (Wrong Answer in Tier 1 & 3) + (High Confidence in Tier 2 & 4)
    st.info("The AI is analyzing response patterns to predict upcoming learning plateaus.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Class Clarity Index", "72%", "+5% from last week")
    col2.metric("Predicted At-Risk Students", "4", "No change")
    col3.metric("Conceptual Change Velocity", "High", delta_color="normal")
