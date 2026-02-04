import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def get_gspread_client():
    # Define the scopes for Sheets and Drive
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Get credentials from Streamlit Secrets
        creds_info = dict(st.secrets["gcp_service_account"])
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
        # Extract the ID from the secret (strips any accidentally pasted URL parts)
        raw_id = st.secrets["general"]["private_gsheets_url"]
        sheet_id = raw_id.split("/d/")[-1].split("/")[0].strip()

        # Step 1: Open the spreadsheet
        try:
            sh = client.open_by_key(sheet_id)
        except Exception:
            # Fallback: try finding by name if the ID lookup fails
            sh = client.open("Chemistry_Research_Data")
            
        # Step 2: Open the 'Participants' tab
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Step 3: Check if User_ID exists (Case-insensitive)
        valid_ids = data['User_ID'].astype(str).str.strip().str.upper().values
        return str(user_id).strip().upper() in valid_ids
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return False

# --- THESE FUNCTIONS ARE REQUIRED BY MAIN_APP.PY TO PREVENT THE IMPORT ERROR ---

def save_quiz_responses(user_id, responses):
    """Saves quiz data - implementation coming in next step."""
    pass

def save_temporal_traces(user_id, traces):
    """Saves user behavior data - implementation coming in next step."""
    pass

def analyze_reasoning_quality(responses):
    """AI analysis placeholder - implementation coming in next step."""
    return "AI Engine Online"
