import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("📊 Researcher Observation Deck")
    client = get_gspread_client()
    if not client: return

    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    tab1, tab2, tab3 = st.tabs(["🕒 Traces", "📚 Audit", "📈 Trends"])

    with tab1:
        # Fetching the raw data for your PhD analysis
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        st.dataframe(traces.tail(15))

    with tab2:
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats)

    with tab3:
        st.subheader("Engagement Statistics")
        # FIXED: Indented block added here to resolve your crash
        if not traces.empty and 'Event' in traces.columns:
            st.bar_chart(traces['Event'].value_counts())
