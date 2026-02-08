import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("---")

    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Class Analytics", "🧩 Misconception Tracker", "📂 Material Audit"])

    # --- TAB 0: DEPLOY LESSONS (Restored) ---
    with tabs[0]:
        st.subheader("Publish New Instructional Module")
        
        with st.form("deployment_form"):
            col1, col2 = st.columns(2)
            with col1:
                mod_name = st.text_input("Module Name", placeholder="e.g., VSEPR Theory")
                group = st.selectbox("Assign to Group", ["Exp_A", "Control"])
                mode = st.selectbox("Instructional Mode", ["AI-Scaffolded", "Traditional"])
            
            with col2:
                uploaded_file = st.file_uploader("Upload Lesson PDF", type="pdf")
                learning_obj = st.text_area("Learning Objective (For AI Context)")

            scaffold_hint = st.text_area("Custom AI Scaffold Hint (Optional)")
            
            submit = st.form_submit_button("Deploy to Student Portals")
            
            if submit:
                if mod_name and uploaded_file:
                    save_deployment(mod_name, group, mode, learning_obj)
                    st.success(f"Successfully deployed '{mod_name}' to {group}!")
                else:
                    st.error("Please provide a module name and a PDF file.")

    # --- TAB 1: CLASS ANALYTICS (Fixed) ---
    with tabs[1]:
        render_class_analytics()

    # --- TAB 2: MISCONCEPTION TRACKER ---
    with tabs[2]:
        st.subheader("🧩 Conceptual Change Monitor")
        st.info("This tool identifies students with 'Correct' answers but 'Incorrect' reasoning.")

    # --- TAB 3: MATERIAL AUDIT ---
    with tabs[3]:
        render_audit_logs()

def render_class_analytics():
    st.subheader("📊 Class Analytics & Engagement")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            c1, c2 = st.columns(2)
            # Safe check for Tier_4 to avoid the previous error
            tier4_col = 'Tier_4' if 'Tier_4' in logs.columns else logs.columns[-1]
            completions = logs[logs[tier4_col].astype(str).str.strip() != ""].shape[0]
            
            c1.metric("4-Tier Completions", completions)
            c2.metric("Total Entries", len(logs))
            
            st.write("### Tier 1 (Initial Answer) Trends")
            st.bar_chart(logs['Tier_1 (Answer)'].value_counts()) # Matches your header
            
            with st.expander("🔍 Inspect Raw Log Data"):
                st.dataframe(logs)
    except Exception as e:
        st.error(f"Analytics Error: {e}")

def render_audit_logs():
    st.subheader("📂 Published Materials Library")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats)
    except:
        st.warning("No records found.")

def save_deployment(name, group, mode, obj):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), name, group, mode, obj])
    except Exception as e:
        st.error(f"Deployment Log Error: {e}")
