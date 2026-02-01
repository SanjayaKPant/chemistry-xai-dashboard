import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection  # This must be exactly like this

# 1. This defines 'conn' correctly
conn = st.connection("gsheets", type=GSheetsConnection)

def log_temporal_trace(event_name, details=""):
    """Captures micro-moments for Process Mining."""
    if 'trace_buffer' not in st.session_state:
        st.session_state.trace_buffer = []
    
    st.session_state.trace_buffer.append({
        "User_ID": st.session_state.user_data.get('User_ID', 'Unknown'),
        "Timestamp": pd.Timestamp.now().isoformat(),
        "Event": event_name,
        "Details": str(details)
    })

def save_temporal_traces(conn, trace_buffer):
    """Syncs the local session buffer to the Google Sheet."""
    if not trace_buffer:
        return True
        
    try:
        new_traces_df = pd.DataFrame(trace_buffer)
        existing_traces = conn.read(worksheet="Temporal_Traces", ttl=0)
        updated_traces = pd.concat([existing_traces, new_traces_df], ignore_index=True)
        conn.update(worksheet="Temporal_Traces", data=updated_traces)
        
        # Clear buffer locally to prevent duplicates
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
