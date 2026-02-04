import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    """PhD-Grade Authentication for the Research Lab."""
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        # Load the dictionary from Secrets
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # CRITICAL: Convert escaped newlines back to actual newlines
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        # Authorize the client
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Critical Infrastructure Error: {e}")
        return None

def check_login(user_id):
    """Verifies User_ID against the research participants database."""
    client = get_gspread_client()
    if not client: return False
    try:
        sheet_url = st.secrets["general"]["private_gsheets_url"]
        sh = client.open_by_key(sheet_url)
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        return str(user_id) in data['User_ID'].astype(str).values
    except Exception as e:
        st.error(f"Database Query Failed: {e}")
        return False

# Module stubs for future data collection
def save_quiz_responses(u, r): pass
def save_temporal_traces(u, t): pass
def analyze_reasoning_quality(r): return "Engine Ready"
