import streamlit as st
import gspread
import pandas as pd
import base64
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        # Decode the Base64 key into a standard string in-memory
        encoded_key = st.secrets["private_key_base64"]
        decoded_key = base64.b64decode(encoded_key).decode("utf-8")
        
        creds_info = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": decoded_key,
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
        st.error(f"Base64 Auth Failed: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return False
    try:
        sh = client.open_by_key(st.secrets["private_gsheets_url"])
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        return str(user_id) in data['User_ID'].astype(str).values
    except Exception as e:
        st.error(f"Sheet Access Error: {e}")
        return False

# Function placeholders
def save_quiz_responses(u, r): pass
def save_temporal_traces(u, t): pass
def analyze_reasoning_quality(r): return "Pending"
