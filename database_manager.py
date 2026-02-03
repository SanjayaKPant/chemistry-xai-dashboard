import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd

import base64

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        # Build the credentials info exactly as it appears in secrets
        creds_info = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
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
        st.error(f"Authentication Error: {e}")
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
