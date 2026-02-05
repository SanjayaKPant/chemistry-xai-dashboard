import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(credentials) 
        return client
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return None
    try:
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants")
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Standardize for matching
        search_id = str(user_id).strip().upper()
        data['User_ID'] = data['User_ID'].astype(str).str.strip().upper()
        
        user_row = data[data['User_ID'] == search_id]
        
        if not user_row.empty:
            return {
                "id": user_row.iloc[0]['User_ID'],
                "password": str(user_row.iloc[0]['Password']), # Column B
                "name": user_row.iloc[0]['Name'],             # Column C
                "role": user_row.iloc[0]['Role'],             # Column D
                "group": user_row.iloc[0]['Group']            # Column E
            }
        return None
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

def log_temporal_trace(user_id, action):
    """Automatically logs user activity to the Temporal_Traces tab."""
    client = get_gspread_client()
    if client:
        try:
            sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
            sh = client.open_by_key(sheet_id)
            trace_sheet = sh.worksheet("Temporal_Traces")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            trace_sheet.append_row([user_id, action, now])
        except:
            pass # Silent fail to not interrupt user experience

def analyze_reasoning_quality(responses):
    return "AI Engine Online"
