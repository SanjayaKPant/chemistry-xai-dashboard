import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- AUTHENTICATION ---
def get_creds():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

def get_gspread_client():
    creds = get_creds()
    return gspread.authorize(creds) if creds else None

# --- PhD RESEARCH LOGGERS ---

def log_assessment(user_id, group, module_id, t1, t2, t3, t4, status, timestamp, t5="", t6="", diag_res="Pending", misc_tag="None"):
    """Logs the 12-column Metacognitive Journey."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assessment_Logs")
        
        # Order: Timestamps, User_ID, Group, Module_ID, T1, T2, T3, T4, T5, T6, Result, Tag
        row = [timestamp, user_id, group, module_id, t1, t2, t3, t4, t5, t6, diag_res, misc_tag]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Assessment Log Error: {e}")
        return False

def log_temporal_trace(user_id, event_type, details):
    """Logs AI-Student dialogue for qualitative analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, event_type, details])
        return True
    except:
        return False

# --- KEEP YOUR EXISTING LOGIN/MATERIAL FUNCTIONS BELOW ---
def check_login(user_id):
    client = get_gspread_client()
    try:
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        df['User_ID'] = df['User_ID'].astype(str).str.upper()
        match = df[df['User_ID'] == str(user_id).upper()]
        return match.iloc[0].to_dict() if not match.empty else None
    except: return None
