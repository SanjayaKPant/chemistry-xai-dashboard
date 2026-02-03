import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        # Pull info and convert text \n into real newlines
        info = dict(st.secrets)
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        # Ensure only Google credentials remain in the dict
        valid_keys = ["type", "project_id", "private_key_id", "private_key", 
                      "client_email", "client_id", "auth_uri", "token_uri", 
                      "auth_provider_x509_cert_url", "client_x509_cert_url"]
        creds_dict = {k: info[k] for k in valid_keys if k in info}
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Morning Auth Attempt Failed: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return False
    try:
        sh = client.open_by_key(st.secrets["private_gsheets_url"])
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        # Convert everything to string for a reliable match
        return str(user_id) in data['User_ID'].astype(str).values
    except Exception as e:
        st.error(f"Sheet Access Error: {e}")
        return False

# Function placeholders for main_app.py
def save_quiz_responses(u, r): pass
def save_temporal_traces(u, t): pass
def analyze_reasoning_quality(r): return "Pending"
