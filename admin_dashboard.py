import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_temporal_traces # This is the bridge to GSheets

def show_admin_portal(conn):
    st.title("📊 Researcher Management Console")
    
    # Check if there is data waiting to be saved
    buffer_size = len(st.session_state.get('trace_buffer', []))
    st.info(f"Current session has **{buffer_size}** unsynced traces.")

    if st.button("🚀 Push Traces to Google Drive"):
        if buffer_size > 0:
            # This calls the function that actually writes to your Drive
            success = save_temporal_traces(conn, st.session_state.trace_buffer)
            if success:
                st.success("Successfully synced to Google Drive!")
        else:
            st.warning("No new data to sync.")

    st.divider()
    
    # View what is already in the Drive
    if st.checkbox("Show Live Data from Drive"):
        live_data = conn.read(worksheet="Temporal_Traces", ttl=0)
        st.dataframe(live_data)
