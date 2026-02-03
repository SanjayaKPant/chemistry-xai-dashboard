import json
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    
    try:
        # Load the raw JSON string from secrets
        creds_json = st.secrets["gcp_service_account"]["json_creds"]
        creds_info = json.loads(creds_json)
        
        # Authenticate using the dictionary we just loaded
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None
