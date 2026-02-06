import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("📊 Researcher Monitoring & Analytics")
    st.markdown("### Experimental Oversight Hub")

    # 1. Access the Shared Drive & Sheet Data
    client = get_gspread_client()
    if not client:
        st.error("Connection to research database failed.")
        return

    sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
    sh = client.open_by_key(sheet_id)

    # 2. Vertical Exploration: Three-Layer Analytics
    tab1, tab2, tab3 = st.tabs(["🕒 Temporal Traces", "📚 Instructional Audit", "👥 Cohort Metrics"])

    with tab1:
        st.subheader("Real-Time Engagement Stream")
        # Captures every 'Log Access' and 'Read Hint' action from student_portal
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        st.dataframe(traces.tail(15), use_container_width=True)

    with tab2:
        st.subheader("Materials Distribution")
        # Monitors if the teacher correctly categorized files as Traditional vs AI
        materials = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.table(materials[['Timestamp', 'Group', 'Title', 'Mode']])

    with tab3:
        st.subheader("Cohort Activity Comparison")
        # Visual proof for your paper: comparing usage frequency between groups
        if not traces.empty:
            st.bar_chart(traces.groupby('User_ID').size())
