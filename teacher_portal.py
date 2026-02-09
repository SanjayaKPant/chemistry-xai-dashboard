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
    st.subheader("🚀 Strategic Lesson Deployment")
    
    # Differentiation: Select the group first to morph the form
    group_choice = st.selectbox("Select Target Research Group", ["Exp_A (Socratic AI)", "Control (Traditional)"])
    group_id = "Exp_A" if "Exp_A" in group_choice else "Control"

    with st.form("deploy_form", clear_on_submit=True):
        st.markdown(f"### 📝 Configuring Module for: **{group_id}**")
        title = st.text_input("Lesson Title (e.g., Bronsted-Lowry Theory)")
        file_link = st.text_input("Material Link (PDF/Drive URL)")
        learning_obj = st.text_area("Learning Objectives")

        # Decision Tree Logic for Experimental Group Only
        socratic_logic = ""
        if group_id == "Exp_A":
            st.markdown("---")
            st.markdown("### 🌳 Socratic Decision Tree")
            st.caption("Define the 'If-Then' logic for the AI to follow during chat.")
            col1, col2 = st.columns(2)
            with col1:
                if_mis = st.text_input("IF Student holds this misconception:", placeholder="e.g., Acids are always liquids")
            with col2:
                then_ask = st.text_input("THEN AI should ask this pivot:", placeholder="e.g., What about Vitamin C (Ascorbic acid) crystals?")
            socratic_logic = f"IF: {if_mis} | THEN: {then_ask}"
        else:
            st.info("ℹ️ Control Group will receive a standard digital interface without AI intervention.")

        if st.form_submit_button("Deploy Research Module"):
            if title and file_link:
                save_deployment(title, group_id, file_link, learning_obj, socratic_logic)
                st.success(f"Successfully deployed to {group_id}!")
            else:
                st.warning("Title and File Link are mandatory.")

def save_deployment(title, group, file, obj, logic):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        # Timestamp, Teacher_ID, Group, Title, Description (Logic), File_Link, Learning_Objectives
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), "Admin_Teacher", group, title, logic, file, obj])
    except Exception as e:
        st.error(f"Save Error: {e}")

def render_class_analytics():
    st.subheader("📊 Comparative Analytics")
    # ... (Same as previous version, pulling from Assessment_Logs)

def render_misconception_tracker():
    st.subheader("🧩 Diagnostic Tracker")
    # ... (Same as previous version)

def render_audit_logs():
    st.subheader("📂 Audit Logs")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats)
    except: st.warning("No data.")
