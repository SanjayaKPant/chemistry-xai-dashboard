import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from credentials_store import get_service_account_info # This is the "Different" thinking

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        # We grab the info directly from our Python file, not the buggy UI
        creds_info = get_service_account_info()
        
        # Ensure newlines are handled correctly
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Authentication Failed: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return False
    try:
        # Keep ONLY the Sheet URL in secrets
        sheet_url = st.secrets["private_gsheets_url"]
        sh = client.open_by_key(sheet_url)
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        return user_id in data['User_ID'].values
    except Exception as e:
        st.error(f"Sheet Error: {e}")
        return False
