import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return False
    try:
        sheet_id = st.secrets["general"]["private_gsheets_url"]
        
        # Phase 1: Try to open the file
        try:
            sh = client.open_by_key(sheet_id)
        except Exception:
            st.error("Diagnostic: Spreadsheet ID not found or not shared with the new API email.")
            return False
            
        # Phase 2: Try to find the tab
        try:
            worksheet = sh.worksheet("Participants") 
        except Exception:
            st.error("Diagnostic: Tab named 'Participants' not found in your Google Sheet.")
            return False
            
        data = pd.DataFrame(worksheet.get_all_records())
        return str(user_id) in data['User_ID'].astype(str).values
    except Exception as e:
        st.error(f"General Query Error: {e}")
        return False

# Placeholder stubs
def save_quiz_responses(u, r): pass
def save_temporal_traces(u, t): pass
def analyze_reasoning_quality(r): return "Engine Ready"
