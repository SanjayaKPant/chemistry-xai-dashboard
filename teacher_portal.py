import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("---")

    # Creating the tabs for your different tools
    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Class Analytics", "🧩 Misconception Tracker", "📂 Material Audit"])

    with tabs[0]:
        # This is your existing deployment code
        st.subheader("Publish New Instructional Module")
        # ... (keep your existing deployment logic here)

    with tabs[1]:
        render_class_analytics()

    with tabs[2]:
        st.subheader("🧩 Conceptual Change Monitor")
        st.info("Analyzing student responses for scientific misconceptions.")

    with tabs[3]:
        render_audit_logs()

def render_class_analytics():
    st.subheader("📊 Class Analytics & Engagement")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Pull data from Assessment_Logs
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            col1, col2 = st.columns(2)
            
            # Robust check for Tier_4
            if 'Tier_4' in logs.columns:
                completions = logs[logs['Tier_4'].astype(str).str.strip() != ""].shape[0]
                col1.metric("4-Tier Completions", completions)
            else:
                col1.metric("4-Tier Completions", "0")
                st.warning("⚠️ Column 'Tier_4' not detected. Check your spreadsheet headers.")

            col2.metric("Total Entries", len(logs))
            
            # Show the actual data for debugging
            with st.expander("🔍 Inspect Raw Log Data"):
                st.dataframe(logs)
                
        else:
            st.info("Awaiting data from student participants...")
            
    except Exception as e:
        st.error(f"Analytics Error: {e}")

def render_audit_logs():
    """Defines the previously missing function to fix the NameError"""
    st.subheader("📂 Published Materials Library")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats, use_container_width=True)
    except:
        st.warning("No records found in Instructional_Materials.")
