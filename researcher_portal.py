import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    """Main entry point for the Researcher Gate."""
    st.title("📊 Research Observation Deck")
    st.markdown("### Evidence-Based Monitoring for PhD Analysis")

    # 1. Secure Database Connection
    client = get_gspread_client()
    if not client:
        st.error("Connection to Google Sheets failed. Check your API credentials.")
        return

    # Use your specific Sheet ID
    sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
    
    try:
        sh = client.open_by_key(sheet_id)
        
        # 2. Horizontal Exploration: Organizing Research Data
        tab1, tab2, tab3 = st.tabs(["🕒 Student Trace Logs", "📚 Material Audit", "📉 Comparative Metrics"])

        with tab1:
            st.subheader("Live Temporal Traces")
            st.caption("Tracking student interactions for behavioral analysis.")
            # Fetch the trace data you successfully set up
            trace_data = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            if not trace_data.empty:
                st.dataframe(trace_data.tail(20), use_container_width=True)
            else:
                st.info("No student activity recorded yet.")

        with tab2:
            st.subheader("Instructional Materials Overview")
            # Audit the Shared Drive links and groups
            mat_data = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
            st.dataframe(mat_data, use_container_width=True)

        with tab3:
            st.subheader("Experimental Fidelity Check")
            # Vertical Depth: Proving Plan A/B isolation for journals
            if not trace_data.empty:
                # Group data to see which experimental group is more active
                activity_counts = trace_data.groupby('Action').size()
                st.bar_chart(activity_counts)
            else:
                st.write("Waiting for data to generate comparison charts.")

    except Exception as e:
        st.error(f"Error accessing research sheets: {e}")

# This ensures the researcher_portal can be called by main_app.py
if __name__ == "__main__":
    show()
