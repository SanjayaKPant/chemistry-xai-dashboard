import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

def get_gspread_client():
    # This matches the structure of the secrets required by your KeyError logs
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(credentials)

def check_login(user_id):
    try:
        client = get_gspread_client()
        sheet_id = st.secrets["private_gsheets_url"]
        
        # Step 1: Try to open the Spreadsheet
        try:
            sh = client.open_by_key(sheet_id)
        except Exception:
            return st.error(f"❌ Spreadsheet ID not found. Check if the ID '{sheet_id}' is correct and shared with the client_email.")

        # Step 2: Try to open the Worksheet
        try:
            worksheet = sh.worksheet("Participants")
        except Exception:
            return st.error("❌ Worksheet 'Participants' not found. Check your Tab names at the bottom of the Google Sheet.")

        records = pd.DataFrame(worksheet.get_all_records())
        user = records[records['User_ID'] == user_id]
        
        if not user.empty:
            st.session_state.user_data = user.iloc[0].to_dict()
            st.session_state.logged_in = True
            return True
        else:
            st.warning("User ID not found in the 'Participants' list.")
            return False
            
    except Exception as e:
        st.error(f"General Sync Error: {e}")
        return False

def save_quiz_responses(data):
    client = get_gspread_client()
    sheet = client.open_by_key(st.secrets["private_gsheets_url"]).worksheet("Responses")
    sheet.append_row(list(data.values()))
    return True

def save_temporal_traces(trace_list):
    if not trace_list: return
    client = get_gspread_client()
    sheet = client.open_by_key(st.secrets["private_gsheets_url"]).worksheet("Temporal_Traces")
    for trace in trace_list:
        sheet.append_row(list(trace.values()))
    return True

def analyze_reasoning_quality(text):
    # NLP Keyword scoring from your research requirements
    keywords = ["probability", "cloud", "orbital", "energy", "nucleus", "distance", "level"]
    found = [w for w in keywords if w in text.lower()]
    score = len(found)
    return score, ", ".join(found)
