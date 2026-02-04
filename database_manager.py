import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    """Authenticates and returns the Google Sheets client."""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Load credentials from Streamlit Secrets
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        
        # Authorize and create the 'client' variable
        client = gspread.authorize(credentials) 
        return client
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

def check_login(user_id):
    """Verifies User_ID and returns Role/Group data."""
    client = get_gspread_client()
    if not client: return None
    try:
        # Get Sheet ID from your private URL secret
        raw_url = st.secrets["general"]["private_gsheets_url"]
        sheet_id = raw_url.split("/d/")[-1].split("/")[0].strip()
        
        sh = client.open_by_key(sheet_id)
        # IMPORTANT: Ensure your Google Sheet tab is named 'Participants'
        worksheet = sh.worksheet("Participants")
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Clean data for matching
        data['User_ID'] = data['User_ID'].astype(str).str.strip().str.upper()
        search_id = str(user_id).strip().upper()
        
        user_row = data[data['User_ID'] == search_id]
        
        if not user_row.empty:
            return {
                "id": user_row.iloc[0]['User_ID'],
                "name": user_row.iloc[0]['Name'],
                "role": user_row.iloc[0]['Role'],
                "group": user_row.iloc[0]['Group']
            }
        return None
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return None

def analyze_reasoning_quality(responses):
    """Placeholder for your AI Misconception Detection logic."""
    return "AI Engine Online & Monitoring"
