import streamlit as st
import pandas as pd

def save_temporal_traces(conn, trace_buffer):
    """
    Specifically handles the 'High-Fidelity Temporal Traces'.
    Syncs the local session buffer to the Google Sheet.
    """
    if not trace_buffer:
        return True # Nothing to sync, so no error
        
    try:
        # 1. Convert buffer to DataFrame
        new_traces_df = pd.DataFrame(trace_buffer)
        
        # 2. Append to the specific GSheet tab
        # Note: Ensure the tab 'Temporal_Traces' exists in your GSheet
        existing_traces = conn.read(worksheet="Temporal_Traces", ttl=0)
        updated_traces = pd.concat([existing_traces, new_traces_df], ignore_index=True)
        conn.update(worksheet="Temporal_Traces", data=updated_traces)
        
        # 3. Clear the buffer locally to prevent duplicate saves
        st.session_state.trace_buffer = []
        return True
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return False

def save_quiz_responses(conn, data_dict):
    """Saves the static 4-tier quiz answers."""
    try:
        df = pd.DataFrame([data_dict])
        existing = conn.read(worksheet="Responses", ttl=0)
        updated = pd.concat([existing, df], ignore_index=True)
        conn.update(worksheet="Responses", data=updated)
        return True
    except Exception as e:
        st.error(f"Data Save Error: {e}")
        return False
