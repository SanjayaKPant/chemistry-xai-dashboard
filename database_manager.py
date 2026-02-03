import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd

def get_gspread_client():
    """Authenticates with Google Sheets using the flattened JSON secret."""
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        # Load the raw JSON string from secrets
        creds_json = st.secrets["gcp_service_account"]["json_creds"]
        creds_info = json.loads(creds_json)
        
        # Authenticate
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None

def check_login(user_id):
    """Checks if the User ID exists in the 'Participants' tab."""
    client = get_gspread_client()
    if not client:
        return False
    try:
        # Connect to your specific sheet
        sheet_url = st.secrets["private_gsheets_url"]
        sh = client.open_by_key(sheet_url)
        worksheet = sh.worksheet("Participants") # Must match your tab name exactly
        
        data = pd.DataFrame(worksheet.get_all_records())
        return user_id in data['User_ID'].values
    except Exception as e:
        st.error(f"Login Check Error: {e}")
        return False

# Placeholder functions to resolve the ImportError in main_app.py
def save_quiz_responses(user_id, responses):
    st.info("Quiz response saving logic goes here.")
    pass

def save_temporal_traces(user_id, traces):
    pass

def analyze_reasoning_quality(responses):
    return "Analysis pending..."
