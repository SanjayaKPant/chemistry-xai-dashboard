import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# --- GOOGLE CLIENTS ---
def get_creds():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_info = dict(st.secrets["gcp_service_account"])
    creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(creds_info, scopes=scope)

def get_gspread_client():
    try:
        return gspread.authorize(get_creds())
    except Exception as e:
        st.error(f"GSheets Auth Error: {e}")
        return None

def get_drive_service():
    try:
        return build('drive', 'v3', credentials=get_creds())
    except Exception as e:
        st.error(f"GDrive Auth Error: {e}")
        return None

# --- DATABASE LOGIC ---
def check_login(user_id):
    client = get_gspread_client()
    if not client: return None
    try:
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants")
        data = pd.DataFrame(worksheet.get_all_records())
        
        # THE FIX: We must use .str before .upper() to handle the whole column
        data['User_ID'] = data['User_ID'].astype(str).str.strip().str.upper()
        
        # Clean the input from the login screen
        search_id = str(user_id).strip().upper()
        
        # Look for the user
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
        # This is where the red error box in your screenshot is coming from
        st.error(f"Login Error: {e}")
        return None

# --- SYSTEMATIC FILE ORGANIZATION ---
def upload_and_log_material(teacher_id, group, title, mode, file_obj, desc, hint):
    drive_service = get_drive_service()
    gs_client = get_gspread_client()
    
    if not drive_service or not gs_client: return False
    
    try:
        # 1. Upload to Drive
        file_metadata = {'name': f"[{group}] {title}.pdf"}
        media = MediaIoBaseUpload(io.BytesIO(file_obj.getvalue()), mimetype='application/pdf')
        
        drive_file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        # Set to 'Anyone with link can view'
        drive_service.permissions().create(
            fileId=drive_file.get('id'), 
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()
        
        file_link = drive_file.get('webViewLink')

        # 2. Log to GSheets 'Instructional_Materials'
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = gs_client.open_by_key(sheet_id)
        # Ensure you created this tab!
        worksheet = sh.worksheet("Instructional_Materials") 
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, teacher_id, group, title, mode, file_link, desc, hint])
        return True
    except Exception as e:
        st.error(f"Systematic Upload Failed: {e}")
        return False

def log_temporal_trace(user_id, action):
    client = get_gspread_client()
    if client:
        try:
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            worksheet = sh.worksheet("Temporal_Traces") #
            worksheet.append_row([user_id, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except: pass
