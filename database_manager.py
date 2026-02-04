import streamlit as st
import gspread
import pandas as pd
import re
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Auth Config Error: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return False
    try:
        raw_id = st.secrets["general"]["private_gsheets_url"]
        
        # CLEANUP: Extract ID if user accidentally pasted the full URL
        if "spreadsheets/d/" in raw_id:
            sheet_id = raw_id.split("spreadsheets/d/")[1].split("/")[0]
        else:
            sheet_id = raw_id.strip()

        # Step 1: Open Spreadsheet
        try:
            sh = client.open_by_key(sheet_id)
        except Exception as e:
            st.error(f"Access Denied: Is the Sheets API enabled for project 'phd-research-486400'? Error: {e}")
            return False
            
        # Step 2: Open Worksheet
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Clean ID strings for comparison
        target_id = str(user_id).strip().upper()
        existing_ids = data['User_ID'].astype(str).str.strip().str.upper().values
        
        return target_id in existing_ids
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return False

# Module stubs
def save_quiz_responses(u, r): pass
def save_temporal_traces(u, t): pass
def analyze_reasoning_quality(r): return "System Online"
