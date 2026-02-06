import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("📊 Researcher Analytics & Monitoring")
    st.info("This portal provides real-time oversight of experimental fidelity and student engagement.")

    client = get_gspread_client()
    if not client:
        st.error("Database connection failed.")
        return

    sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60" #
    sh = client.open_by_key(sheet_id)

    # --- VERTICAL EXPLORATION: DATA MONITORING ---
    tab1, tab2, tab3 = st.tabs(["Temporal Traces", "Material Logs", "Cohort Stats"])

    with tab1:
        st.subheader("🕒 Live Interaction Feed")
        try:
            # Fetches the raw temporal data for PhD analysis
            trace_data = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            st.dataframe(trace_data.tail(20), use_container_width=True)
        except:
            st.warning("No trace data recorded yet.")

    with tab2:
        st.subheader("📁 Published Instructional Materials")
        # Verification of Plan A vs Plan B distribution
        mat_data = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mat_data, use_container_width=True)

    with tab3:
        st.subheader("📈 Experimental vs. Control Analysis")
        # Vertical Depth: Aggregating counts for journal-ready reporting
        if not trace_data.empty:
            st.bar_chart(trace_data['Action'].value_counts())
