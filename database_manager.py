import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# This explicitly tells the connection to look for the [gsheets] section in Secrets
# Standard initialization - it will find the URL in your secrets automatically
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
    if not trace_buffer:
        return True
    try:
        new_traces_df = pd.DataFrame(trace_buffer)
        # Explicitly tell it which spreadsheet to use from secrets
        conn.update(worksheet="Temporal_Traces", data=new_traces_df, 
                    spreadsheet=st.secrets["gsheets"]["public_gsheets_url"])
        st.session_state.trace_buffer = [] 
        return True
    except Exception as e:
        st.error(f"Sync Error: {e}")
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
