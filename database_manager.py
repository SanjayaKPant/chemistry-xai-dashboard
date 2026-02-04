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
        # Use the ID from your screenshot URL
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60" 
        sh = client.open_by_key(sheet_id)
        
        # Ensure tab name matches exactly
        worksheet = sh.worksheet("Participants")
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
        st.error(f"Database Error: {e}")
        return None

# FIX FOR THE IMPORT ERROR
def analyze_reasoning_quality(responses):
    """Placeholder for your Misconception Detection logic."""
    return "AI Reasoning Engine Online"
