import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    # We include both Sheets and Drive scopes to ensure the 'Search' function works
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        # Fix formatting for the private key
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Authentication Config Error: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return False
    
    try:
        # 1. Clean the ID aggressively (removing spaces, newlines, or full URL parts)
        raw_id = st.secrets["general"]["private_gsheets_url"]
        sheet_id = raw_id.split("/d/")[-1].split("/")[0].strip()
        
        # 2. Try to open the sheet
        try:
            sh = client.open_by_key(sheet_id)
        except Exception:
            # BACKUP: Try to find the sheet by its exact name if ID fails
            try:
                sh = client.open("Chemistry_Research_Data")
            except Exception as e:
                st.error(f"Google cannot find the sheet. Please ensure the email '{client.auth.service_account_email}' is an Editor.")
                return False
            
        # 3. Access the tab
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        
        # 4. Final ID check (Case-insensitive)
        user_list = data['User_ID'].astype(str).str.strip().tolist()
        return str(user_id).strip() in user_list

    except Exception as e:
        st.error(f"Final Query Error: {e}")
        return False

# Placeholder stubs for your research tracking
def save_quiz_responses(u, r): pass
def save_temporal_traces(u, t): pass
