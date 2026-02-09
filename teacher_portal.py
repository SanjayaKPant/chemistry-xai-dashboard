import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("---")

    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Class Analytics", "🧩 Misconception Tracker", "📂 Material Audit"])

    with tabs[0]: render_deploy_lessons()
    with tabs[1]: render_class_analytics()
    with tabs[2]: render_misconception_tracker()
    with tabs[3]: render_audit_logs()

def render_deploy_lessons():
    st.subheader("Publish New Instructional Module")
    with st.form("deployment_form"):
        col1, col2 = st.columns(2)
        with col1:
            mod_name = st.text_input("Module Name", placeholder="e.g., Covalent Bonding")
            group = st.selectbox("Assign to Group", ["Exp_A", "Control"])
        with col2:
            uploaded_file = st.file_uploader("Upload Lesson PDF", type="pdf")
            mode = st.selectbox("Instructional Mode", ["AI-Scaffolded (Experimental)", "Traditional (Control)"])
        
        # 🔬 RESEARCH IMPROVISATION: Target Misconception
        target_error = st.text_input("Target Misconception", placeholder="e.g., Atoms 'want' to fill shells")
        
        submit = st.form_submit_button("Deploy to Student Portals")
        if submit and mod_name and uploaded_file:
            save_deployment(mod_name, group, mode, target_error)
            st.success(f"Deployed {mod_name} to {group} targeting: {target_error}")

def render_class_analytics():
    st.subheader("📊 Comparative Engagement Metrics")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            # 🔬 RESEARCH IMPROVISATION: Comparative View
            exp_data = logs[logs['Group'] == 'Exp_A']
            ctrl_data = logs[logs['Group'] == 'Control']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Exp Group Active", len(exp_data))
            c2.metric("Control Group Active", len(ctrl_data))
            
            # Completion Rate Calculation
            comp_rate = (logs['Tier_4 (Confidence_Reas)'].notna().sum() / len(logs)) * 100
            c3.metric("Overall Completion", f"{comp_rate:.1f}%")

            st.write("### Engagement: Experimental vs Control")
            chart_data = logs.groupby(['Group', 'Module_ID']).size().unstack().fillna(0)
            st.area_chart(chart_data)
        else:
            st.info("Awaiting participant data...")
    except Exception as e:
        st.error(f"Analytics Error: {e}")

def render_misconception_tracker():
    st.subheader("🧩 Conceptual Change Engine")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())

        if not logs.empty:
            # 🔬 RESEARCH IMPROVISATION: Identifying 'Hard-to-Change' Concepts
            st.write("### ⚠️ Resistance to Change (High Confidence Errors)")
            # Filter: Correct Tier 1 but Wrong Tier 3 + High Confidence = False Understanding
            resistance = logs[(logs['Diagnostic_Result'] == 'Misconception') & 
                              (logs['Tier_4 (Confidence_Reas)'].astype(str).str.contains("High|5"))]
            
            if not resistance.empty:
                st.warning(f"Critical: {len(resistance)} instances of High-Confidence Misconceptions detected.")
                st.dataframe(resistance[['User_ID', 'Module_ID', 'Misconception_Tag', 'Group']])
            
            st.write("### Full Diagnostic Log")
            st.dataframe(logs[['Timestamps', 'User_ID', 'Diagnostic_Result', 'Misconception_Tag', 'Group']])
    except Exception as e:
        st.error(f"Tracker Error: {e}")

def render_audit_logs():
    st.subheader("📂 Instructional Material Audit")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.table(mats) # Using table for better audit readability
    except:
        st.warning("No deployment records found.")

def save_deployment(name, group, mode, error):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        # Added 'Target_Misconception' to the row
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), name, group, mode, error])
    except Exception as e:
        st.error(f"Deployment Error: {e}")
