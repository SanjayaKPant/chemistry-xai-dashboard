import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(credentials) 
        return client
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None
def check_login(user_id):
    client = get_gspread_client()
    if not client: return None
    try:
        raw_url = st.secrets["general"]["private_gsheets_url"]
        # Standardize ID extraction
        sheet_id = raw_url.split("/d/")[-1].split("/")[0].strip()
        
        # Try to open the sheet
        try:
            sh = client.open_by_key(sheet_id)
        except Exception:
            st.error(f"404: Could not find the Spreadsheet. Check the ID in Secrets: {sheet_id}")
            return None

        # Try to open the tab
        try:
            worksheet = sh.worksheet("Participants")
        except Exception:
            st.error("404: Could not find the tab named 'Participants'. Please check for trailing spaces!")
            return None

        data = pd.DataFrame(worksheet.get_all_records())
        search_id = str(user_id).strip().upper()
        user_row = data[data['User_ID'].astype(str).str.strip().str.upper() == search_id]
        
        if not user_row.empty:
            return {
                "id": user_row.iloc[0]['User_ID'],
                "name": user_row.iloc[0]['Name'],
                "role": user_row.iloc[0]['Role'],
                "group": user_row.iloc[0]['Group']
            }
        return None
    except Exception as e:
        st.error(f"Unexpected Database Error: {e}")
        return None
