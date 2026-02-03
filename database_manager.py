import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        # 1. Clean the private key: convert literal \n into real newlines
        # This fixes the "InvalidByte(1624, 61)" error immediately
        private_key = st.secrets["private_key"].replace("\\n", "\n")
        
        creds_info = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": private_key,
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
        }
        
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"General Sync Error: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client:
        return False
    try:
        # Uses the URL from your secrets
        sheet_url = st.secrets["private_gsheets_url"]
        sh = client.open_by_key(sheet_url)
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        return user_id in data['User_ID'].values
    except Exception as e:
        st.error(f"Login Check Error: {e}")
        return False

# Placeholder functions to keep main_app.py running
def save_quiz_responses(user_id, responses): pass
def save_temporal_traces(user_id, traces): pass
def analyze_reasoning_quality(responses): return "Analysis Pending"
