import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("📊 Research Observation Deck")
    # Fetch live traces to monitor experimental dosage
    client = get_gspread_client()
    sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
    
    traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
    st.subheader("Live Temporal Trace Feed")
    st.dataframe(traces.tail(10), use_container_width=True)
