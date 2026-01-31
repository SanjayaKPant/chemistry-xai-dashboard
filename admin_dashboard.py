import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_temporal_traces 

def show_admin_portal(conn):
    st.title("📊 Researcher Management Console")
    
    # 1. TRACE SYNC SECTION
    # Check if there is data waiting to be saved
    buffer_size = len(st.session_state.get('trace_buffer', []))
    st.info(f"Current session has **{buffer_size}** unsynced traces.")

    if st.button("🚀 Push Traces to Google Drive"):
        if buffer_size > 0:
            success = save_temporal_traces(conn, st.session_state.trace_buffer)
            if success:
                st.success("Successfully synced to Google Drive!")
        else:
            st.warning("No new data to sync.")

    st.divider()
    
    # 2. DATA VISUALIZATION & VERIFICATION
    if st.checkbox("Show Live Data from Drive"):
        try:
            # SAFE-GUARD: Attempt to read the traces
            live_data = conn.read(worksheet="Temporal_Traces", ttl=0)
            
            if not live_data.empty:
                st.subheader("Live Temporal Analytics")
                # Show a quick summary of events (PhD Process Mining)
                fig = px.bar(live_data, x="Event", color="User_ID", title="Event Distribution per User")
                st.plotly_chart(fig, use_container_width=True)
                
                st.write("### Raw Data Table")
                st.dataframe(live_data)
            else:
                st.warning("The 'Temporal_Traces' worksheet is empty.")
                
        except Exception as e:
            # This catches the 'WorksheetNotFound' error and explains it to you
            st.error("⚠️ The 'Temporal_Traces' tab was not found or is inaccessible.")
            st.info("💡 **Required Action:** Go to your Google Sheet and create a tab named exactly `Temporal_Traces` with headers: User_ID, Timestamp, Event, Details.")
