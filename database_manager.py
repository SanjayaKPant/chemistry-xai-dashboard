import streamlit as st
import pandas as pd

def save_temporal_traces(conn, trace_buffer):
    """Pushes local session traces to the 'Temporal_Traces' Google Sheet tab."""
    if not trace_buffer:
        return False
    try:
        # 1. Convert the list of traces to a DataFrame
        new_traces_df = pd.DataFrame(trace_buffer)
        
        # 2. Read the existing sheet to avoid overwriting
        existing_traces = conn.read(worksheet="Temporal_Traces", ttl=0)
        
        # 3. Combine and Update
        updated_df = pd.concat([existing_traces, new_traces_df], ignore_index=True)
        conn.update(worksheet="Temporal_Traces", data=updated_df)
        
        # 4. Clear the buffer so we don't save duplicates
        st.session_state.trace_buffer = []
        return True
    except Exception as e:
        st.error(f"Failed to sync traces to Google Drive: {e}")
        return False
