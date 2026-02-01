import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Establish connection using the Service Account secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def save_quiz_responses(conn, data_dict):
    try:
        df = pd.DataFrame([data_dict])
        # Check commas and parentheses carefully here:
        conn.create(
            spreadsheet=st.secrets["gsheets"]["spreadsheet"],
            worksheet="Responses", 
            data=df
        )
        return True
    except Exception as e:
        st.error(f"Data Save Error: {e}")
        return False

def log_temporal_trace(event_type, details=""):
    trace = {
        "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Event": event_type,
        "Details": str(details)
    }
    st.session_state.trace_buffer.append(trace)

def save_temporal_traces(conn, trace_buffer):
    if not trace_buffer:
        return True
    try:
        new_traces_df = pd.DataFrame(trace_buffer)
        conn.create(
            spreadsheet=st.secrets["gsheets"]["spreadsheet"],
            worksheet="Temporal_Traces", 
            data=new_traces_df
        )
        st.session_state.trace_buffer = [] 
        return True
    except Exception as e:
        st.error(f"Trace Sync Error: {e}")
        return False

def save_quiz_responses(conn, data_dict):
    try:
        df = pd.DataFrame([data_dict])
        conn.create(
            spreadsheet=st.secrets["gsheets"]["spreadsheet"],
            worksheet="Responses", 
            data=df
        )
        return True
    except Exception as e:
        st.error(f"Data Save Error: {e}")
        return False
        )
        return True
    except Exception as e:
        st.error(f"Data Save Error: {e}")
        return False
