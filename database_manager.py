import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- 1. CACHED CONNECTION (Speeds up loading) ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
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

# --- 2. AUTHENTICATION ---
def check_login(user_id):
    try:
        # Use a spinner to show progress during the handshake
        with st.spinner("Authenticating with Research Database..."):
            client = get_gspread_client()
            sh = client.open_by_url(st.secrets["gsheets"]["spreadsheet"])
            worksheet = sh.worksheet("Participants")
            
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            df.columns = df.columns.str.strip()
            df['User_ID'] = df['User_ID'].astype(str).str.strip()
            
            user_row = df[df['User_ID'] == str(user_id).strip().upper()]
            
            if not user_row.empty:
                st.session_state.user_data = user_row.iloc[0].to_dict()
                st.session_state.logged_in = True
                return True
            return False
    except Exception as e:
        st.error(f"Gspread Login Error: {e}")
        return False

# --- 3. SAVE RESPONSES ---
def save_quiz_responses(quiz_data):
    try:
        client = get_gspread_client()
        sh = client.open_by_url(st.secrets["gsheets"]["spreadsheet"])
        worksheet = sh.worksheet("Responses")
        
        row_to_add = [
            quiz_data.get("User_ID"),
            quiz_data.get("Timestamp"),
            quiz_data.get("Tier_1"),
            quiz_data.get("Tier_2"),
            quiz_data.get("Tier_3"),
            quiz_data.get("Tier_4")
        ]
        worksheet.append_row(row_to_add)
        return True
    except Exception as e:
        st.error(f"Save Responses Error: {e}")
        return False

# --- 4. SAVE TRACES ---
def save_temporal_traces(trace_buffer):
    if not trace_buffer:
        return True
    try:
        client = get_gspread_client()
        sh = client.open_by_url(st.secrets["gsheets"]["spreadsheet"])
        worksheet = sh.worksheet("Temporal_Traces")
        
        # Batch append to save time
        rows = [[t.get("User_ID"), t.get("Timestamp"), t.get("Event"), t.get("Details")] for t in trace_buffer]
        worksheet.append_rows(rows)
        return True
    except Exception as e:
        st.error(f"Trace Sync Error: {e}")
        return False
