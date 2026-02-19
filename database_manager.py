import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

# --- GOOGLE CLIENTS & AUTH ---
def get_creds():
    """Fetches credentials with robust multi-line PEM key handling."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("GCP Service Account secrets missing!")
            return None
            
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # This line handles the \n conversion if you didn't use triple quotes
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

def get_gspread_client():
    creds = get_creds()
    return gspread.authorize(creds) if creds else None

# --- CORE LOGIN LOGIC ---
def check_login(user_id):
    """Authenticates users from the Participants sheet."""
    client = get_gspread_client()
    if not client: return None
    try:
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants")
        data = pd.DataFrame(worksheet.get_all_records())
        
        data['User_ID'] = data['User_ID'].astype(str).str.strip().str.upper()
        search_id = str(user_id).strip().upper()
        
        user_row = data[data['User_ID'] == search_id]
        if not user_row.empty:
            return user_row.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None

# --- TEACHER PORTAL FUNCTIONS (FIXES IMPORT ERROR) ---
def save_bulk_concepts(concept_list):
    """Saves multiple chemistry modules from the teacher portal."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        
        rows_to_add = []
        for c in concept_list:
            rows_to_add.append([
                c['title'], c['objectives'], c['video'], 
                c['group'], c['socratic_pivot'], c['q_data']
            ])
        ws.append_rows(rows_to_add)
        return True
    except Exception as e:
        st.error(f"Bulk Save Error: {e}")
        return False

# --- 4-TIER STUDENT RESPONSE LOGGING ---
def log_student_response(user_id, sub_title, group, t1, t2, t3, t4):
    """Logs detailed student diagnostics for PhD analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        worksheet = sh.worksheet("Assessment_Logs")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [user_id, timestamp, group, sub_title, t1, t2, t3, t4]
        worksheet.append_row(new_row)
        return True
    except Exception as e:
        st.error(f"Logging Error: {e}")
        return False

# --- TEMPORAL TRACE LOGGING ---
def log_temporal_trace(user_id, event_type, details=""):
    """Logs session engagement for time-series analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        worksheet = sh.worksheet("Temporal_Traces")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, user_id, event_type, details])
    except:
        pass
