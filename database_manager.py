import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- 1. ESTABLISH ROBUST CONNECTION ---
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    # Map Streamlit secrets to the expected Google format
    secret_dict = {
        "type": st.secrets["gsheets"]["type"],
        "project_id": st.secrets["gsheets"]["project_id"],
        "private_key_id": st.secrets["gsheets"]["private_key_id"],
        "private_key": st.secrets["gsheets"]["private_key"],
        "client_email": st.secrets["gsheets"]["client_email"],
        "client_id": st.secrets["gsheets"]["client_id"],
        "auth_uri": st.secrets["gsheets"]["auth_uri"],
        "token_uri": st.secrets["gsheets"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gsheets"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gsheets"]["client_x509_cert_url"]
    }
    creds = Credentials.from_service_account_info(secret_dict, scopes=scope)
    return gspread.authorize(creds)

# --- 2. UPDATED LOGIN LOGIC ---
def check_login(user_id):
    try:
        client = get_gspread_client()
        # Open by URL to be 100% sure we hit the right file
        sh = client.open_by_url(st.secrets["gsheets"]["spreadsheet"])
        worksheet = sh.worksheet("Participants")
        
        # Get all records as a list of dicts
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        df['User_ID'] = df['User_ID'].astype(str).str.strip()
        user_row = df[df['User_ID'] == str(user_id).strip().upper()]
        
        if not user_row.empty:
            st.session_state.user_data = user_row.iloc[0].to_dict()
            st.session_state.logged_in = True
            return True
        return False
    except Exception as e:
        st.error(f"Ultimate Connection Error: {e}")
        return False

# --- 3. UPDATED SAVE LOGIC ---
def save_quiz_responses(quiz_data):
    try:
        client = get_gspread_client()
        sh = client.open_by_url(st.secrets["gsheets"]["spreadsheet"])
        worksheet = sh.worksheet("Responses")
        # Append row: Values must be in the exact order of your sheet headers
        row_to_add = [
            quiz_data["User_ID"],
            quiz_data["Timestamp"],
            quiz_data["Tier_1"],
            quiz_data["Tier_2"],
            quiz_data["Tier_3"],
            quiz_data["Tier_4"]
        ]
        worksheet.append_row(row_to_add)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False
