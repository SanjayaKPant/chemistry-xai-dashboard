import streamlit as st
import pandas as pd

def save_research_data(conn, responses_df, traces_df):
    """
    The Master Sync Function for PhD Research.
    Saves both static quiz answers and temporal process traces.
    """
    try:
        # 1. Sync Static Responses
        existing_res = conn.read(worksheet="Responses", ttl=0)
        updated_res = pd.concat([existing_res, responses_df], ignore_index=True)
        conn.update(worksheet="Responses", data=updated_res)
        
        # 2. Sync Temporal Traces (Crucial for Theme 9)
        existing_traces = conn.read(worksheet="Temporal_Traces", ttl=0)
        updated_traces = pd.concat([existing_traces, traces_df], ignore_index=True)
        conn.update(worksheet="Temporal_Traces", data=updated_traces)
        
        # Clear local buffer after successful cloud sync
        st.session_state.trace_buffer = []
        return True
    except Exception as e:
        st.error(f"❌ Database Sync Failed: {e}")
        return False
