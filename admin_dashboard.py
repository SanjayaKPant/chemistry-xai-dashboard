import streamlit as st
import pandas as pd
import plotly.express as px # Add this to requirements.txt

def show_admin_portal(conn):
    st.title("📊 Researcher Management Console")
    
    # --- RESEARCH METRICS ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Live Temporal Analytics")
        # Load the traces we saw in the export
        traces = conn.read(worksheet="Temporal_Traces", ttl=0)
        
        if not traces.empty:
            # Calculate time spent per event
            fig = px.timeline(traces, x_start="Timestamp", x_end="Timestamp", y="Event", color="User_ID")
            st.plotly_chart(fig, use_container_width=True)
            

    with col2:
        st.subheader("Data Export")
        if st.button("📥 Sync and Download All Traces"):
            csv = traces.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV for ProM/Disco", data=csv, file_name="research_traces.csv")
