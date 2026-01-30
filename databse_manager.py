import streamlit as st
import pandas as pd

def save_research_data(conn, responses_df, traces_df):
    """
    Modular function to save both static responses and temporal traces.
    Ensures PhD data integrity by appending correctly to GSheets.
    """
    try:
        # Save Quiz Responses
        existing_res = conn.read(worksheet="Responses", ttl=0)
        updated_res = pd.concat([existing_res, responses_df], ignore_index=True)
        conn.update(worksheet="Responses", data=updated_res)
        
        # Save Temporal Traces (Theme 9)
        existing_traces = conn.read(worksheet="Temporal_Traces", ttl=0)
        updated_traces = pd.concat([existing_traces, traces_df], ignore_index=True)
        conn.update(worksheet="Temporal_Traces", data=updated_traces)
        
        return True
    except Exception as e:
        st.error(f"⚠️ Database Sync Error: {e}")
        return False