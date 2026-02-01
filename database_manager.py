import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Establish secure connection
conn = st.connection("gsheets", type=GSheetsConnection)

def save_quiz_responses(data_dict):
    try:
        # Build DataFrame from the dictionary
        df = pd.DataFrame([data_dict])
        
        # Use the specific URL from secrets and explicitly set worksheet
        # ttl=0 ensures we don't hit a cache error
        conn.update(
            spreadsheet=st.secrets["gsheets"]["spreadsheet"],
            worksheet="Responses",
            data=df
        )
        return True
    except Exception as e:
        st.error(f"Data Save Error: {e}")
        return False

def log_temporal_trace(event_type, details=""):
    if 'trace_buffer' not in st.session_state:
        st.session_state.trace_buffer = []
    
    trace = {
        "User_ID": st.session_state.get('user_data', {}).get('User_ID', 'Unknown'),
        "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type,
        "Details": str(details)
    }
    st.session_state.trace_buffer.append(trace)

def save_temporal_traces(trace_buffer):
    if not trace_buffer:
        return True
    try:
        new_traces_df = pd.DataFrame(trace_buffer)
        conn.update(
            spreadsheet=st.secrets["gsheets"]["spreadsheet"],
            worksheet="Temporal_Traces",
            data=new_traces_df
        )
        st.session_state.trace_buffer = []
        return True
    except Exception as e:
        st.error(f"Trace Sync Error: {e}")
        return False
