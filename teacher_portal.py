import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("📊 Researcher Observation Deck")
    
    client = get_gspread_client()
    if not client:
        st.error("Sheet connection failed.")
        return

    sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
    sh = client.open_by_key(sheet_id)

    tab1, tab2, tab3 = st.tabs(["🕒 Activity Traces", "📚 Material Audit", "📈 Trends"])

    with tab1:
        st.subheader("Live Temporal Trace Log")
        # Matches the 'Event' column header in your screenshot
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        st.dataframe(traces, use_container_width=True)

    with tab2:
        st.subheader("Audit: Published Materials")
        try:
            mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
            st.dataframe(mats, use_container_width=True)
        except:
            st.warning("Material sheet is empty.")

    with tab3:
        st.subheader("Engagement Statistics")
        if not traces.empty and 'Event' in traces.columns:
            # Using 'Event' to prevent the KeyError
            st.bar_chart(traces['Event'].value_counts())
        else:
            st.write("Awaiting data for trends.")
