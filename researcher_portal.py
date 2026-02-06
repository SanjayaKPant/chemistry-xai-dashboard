import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("📊 Researcher Observation Deck")
    
    client = get_gspread_client()
    if not client:
        st.error("Connection failed.")
        return

    # PhD Database Connection
    sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
    sh = client.open_by_key(sheet_id)

    tab1, tab2, tab3 = st.tabs(["🕒 Activity Traces", "📚 Material Audit", "📈 Trends"])

    with tab1:
        st.subheader("Live Temporal Trace Log")
        # Visualizing the behavioral data for publication
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        st.dataframe(traces.tail(20), use_container_width=True)

    with tab2:
        st.subheader("Audit: Published Materials")
        # Verifying Plan A/B isolation
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats, use_container_width=True)

    with tab3:
        st.subheader("Engagement Statistics")
        if not traces.empty:
        # Changed from 'Action' to 'Event' to match your sheet headers
        st.bar_chart(traces['Event'].value_counts())
