import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    st.title("📊 Researcher Observation Deck")
    
    client = get_gspread_client()
    if not client:
        st.error("Connection failed.")
        return

    sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60" #
    sh = client.open_by_key(sheet_id)

    tab1, tab2 = st.tabs(["Temporal Traces", "Published Materials"])

    with tab1:
        st.subheader("Live Interaction Feed")
        # Visualizing student behavior for your thesis data
        traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        st.dataframe(traces.tail(15), use_container_width=True)

    with tab2:
        st.subheader("Audit: All Materials")
        # Verifying which group got which file (Fidelity Check)
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats, use_container_width=True)
