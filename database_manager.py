import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# ... (keep your existing get_creds, get_gspread_client, and other functions as they are) ...

def log_assessment(user_id, group, module_id, t1, t2, t3, t4, status, timestamp, t5="", t6="", diag_result="Pending", misc_tag="None"):
    """
    PhD Research Logger: Records the 6-Tier journey + Diagnostic results.
    Expected Columns in Sheet: Timestamps, User_ID, Group, Module_ID, Tier_1, Tier_2, Tier_3, Tier_4, Tier_5, Tier_6, Result, Tag
    """
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assessment_Logs")
        
        # Exact order as per your request
        row = [
            timestamp,      # A: Timestamps
            user_id,        # B: User_ID
            group,          # C: Group
            module_id,      # D: Module_ID
            t1,             # E: Tier_1 (Answer)
            t2,             # F: Tier_2 (Confidence_Ans)
            t3,             # G: Tier_3 (Reason)
            t4,             # H: Tier_4 (Confidence_Reas)
            t5,             # I: Tier_5 (Revised_Reasoning)
            t6,             # J: Tier_6 (Revised_Confidence)
            diag_result,    # K: Diagnostic_Result
            misc_tag        # L: Misconception_Tag
        ]
        
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def log_temporal_trace(user_id, event, details=""):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event, details])
    except: pass
