import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# --- GOOGLE CLIENTS & AUTH ---
def get_creds():
    """Fetches credentials from Streamlit Secrets for Sheets and Drive."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception as e:
        st.error(f"Secret Key Error: {e}")
        return None

def get_gspread_client():
    """Returns an authorized gspread client."""
    creds = get_creds()
    if creds:
        try:
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"GSheets Auth Error: {e}")
    return None

def get_drive_service():
    """Returns an authorized Google Drive service."""
    creds = get_creds()
    if creds:
        try:
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            st.error(f"GDrive Auth Error: {e}")
    return None

# --- CORE LOGIN LOGIC ---
def check_login(user_id):
    """Standardizes ID and verifies credentials from the Participants tab."""
    client = get_gspread_client()
    if not client: return None
    try:
        # Your specific Sheet ID
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants") #
        data = pd.DataFrame(worksheet.get_all_records())
        
        # FIXED: Using .str accessor to prevent 'Series' attribute errors
        data['User_ID'] = data['User_ID'].astype(str).str.strip().str.upper()
        search_id = str(user_id).strip().upper()
        
        user_row = data[data['User_ID'] == search_id]
        
        if not user_row.empty:
            return {
                "id": user_row.iloc[0]['User_ID'],
                "password": str(user_row.iloc[0]['Password']),
                "name": user_row.iloc[0]['Name'],
                "role": user_row.iloc[0]['Role'],
                "group": user_row.iloc[0]['Group']
            }
        return None
    except Exception as e:
        st.error(f"Login Database Error: {e}")
        return None

# --- SYSTEMATIC FILE UPLOAD & LOGGING ---
def upload_and_log_material(teacher_id, group, title, mode, file_obj, desc, hint):
    drive_service = get_drive_service()
    gs_client = get_gspread_client()
    
    # PASTE YOUR FOLDER ID HERE
    TARGET_FOLDER_ID = "1sQkHiMCd_8TBeIqBLTd-uozZ5WIQ-k2a" 

    if not drive_service or not gs_client:
        return False
    
    try:
        st.info("🔄 Uploading to Research Folder...")
        # We add 'parents' to tell Google exactly where to put the file
        file_metadata = {
            'name': f"[{group}] {title}.pdf",
            'parents': [TARGET_FOLDER_ID] 
        }
        
        media = MediaIoBaseUpload(io.BytesIO(file_obj.getvalue()), mimetype='application/pdf')
        
        drive_file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        # ... (keep the rest of the permissions and logging code the same)
# --- RESEARCH TRACE LOGGING ---
def log_temporal_trace(user_id, action):
    """Records every user action for Plan A and Plan B analysis."""
    client = get_gspread_client()
    if client:
        try:
            sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
            sh = client.open_by_key(sheet_id)
            worksheet = sh.worksheet("Temporal_Traces") #
            worksheet.append_row([user_id, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except:
            pass # Fails silently to not disrupt user experience
