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
        
        # Define the client BEFORE returning it
        client = gspread.authorize(credentials) 
        return client
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return None
    try:
        # Extract ID from the secret URL
        raw_url = st.secrets["general"]["private_gsheets_url"]
        sheet_id = raw_url.split("/d/")[-1].split("/")[0].strip()
        
        # Open the spreadsheet
        sh = client.open_by_key(sheet_id)
        
        # ERROR CHECK: Make sure this name matches your Google Sheet tab exactly!
        worksheet = sh.worksheet("Participants") 
        
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Standardize for comparison
        data['User_ID'] = data['User_ID'].astype(str).str.strip().str.upper()
        search_id = str(user_id).strip().upper()
        
        user_row = data[data['User_ID'] == search_id]
        
        if not user_row.empty:
            return {
                "id": user_row.iloc[0]['User_ID'],
                "name": user_row.iloc[0]['Name'],
                "role": user_row.iloc[0]['Role'],
                "group": user_row.iloc[0]['Group']
            }
        return None
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: The tab 'Participants' was not found in your Google Sheet.")
        return None
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

# THIS FUNCTION IS REQUIRED BY MAIN_APP.PY
def analyze_reasoning_quality(data):
    # This is a placeholder for your AI logic
    return "AI Analysis System Active"
