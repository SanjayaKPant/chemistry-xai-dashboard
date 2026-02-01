import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Establish connection using the Service Account secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def save_quiz_responses(conn, data_dict):
    try:
        df = pd.DataFrame([data_dict])
        # Use .update instead of .create to avoid the 400 error
        conn.update(
            spreadsheet=st.secrets["gsheets"]["spreadsheet"],
            worksheet="Responses", 
            data=df
        )
        return True
    except Exception as e:
        st.error(f"Data Save Error: {e}")
        return False

def save_temporal_traces(conn, trace_buffer):
    if not trace_buffer:
        return True
    try:
        new_traces_df = pd.DataFrame(trace_buffer)
        # Use .update here as well
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
