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
    """Fetches credentials for Sheets and Drive with Shared Drive scope."""
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
    creds = get_creds()
    return gspread.authorize(creds) if creds else None

def get_drive_service():
    creds = get_creds()
    return build('drive', 'v3', credentials=creds) if creds else None

# --- CORE LOGIN LOGIC ---
def check_login(user_id):
    """Verifies credentials and fixes the 'Series' attribute error."""
    client = get_gspread_client()
    if not client: return None
    try:
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants")
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Standardizing ID format to prevent login failures
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
    """Uploads to Shared Drive to bypass the 403 Quota Error."""
    drive_service = get_drive_service()
    gs_client = get_gspread_client()
    
    # YOUR NEW SHARED DRIVE ID
    TARGET_DRIVE_ID = "0AJAe9AoSTt6-Uk9PVA" 

    if not drive_service or not gs_client: return False
    
    try:
        st.info("🔄 Uploading to Shared Research Drive...")
        
        file_metadata = {
            'name': f"[{group}] {title}.pdf",
            'parents': [TARGET_DRIVE_ID] 
        }
        
        media = MediaIoBaseUpload(io.BytesIO(file_obj.getvalue()), mimetype='application/pdf')
        
        # supportsAllDrives=True is the key to using the Shared Drive's quota
        drive_file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        
        # Grant permissions so participants can view the material
        drive_service.permissions().create(
            fileId=drive_file.get('id'), 
            body={'type': 'anyone', 'role': 'viewer'},
            supportsAllDrives=True
        ).execute()
        
        file_link = drive_file.get('webViewLink')

        # Log metadata to the Spreadsheet for Plan A/B analysis
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = gs_client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Instructional_Materials") 
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, teacher_id, group, title, mode, file_link, desc, hint])
        
        return True
    except Exception as e:
        st.error(f"❌ Systematic Error: {e}")
        return False

def log_temporal_trace(user_id, action):
    """Records user actions for research data integrity."""
    client = get_gspread_client()
    if client:
        try:
            sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
            sh = client.open_by_key(sheet_id)
            worksheet = sh.worksheet("Temporal_Traces") 
            worksheet.append_row([user_id, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except: pass

def get_materials_by_group(group_name):
    """Fetches materials and handles missing column errors gracefully."""
    client = get_gspread_client()
    if not client: return []
    try:
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Instructional_Materials")
        records = worksheet.get_all_records()
        
        if not records:
            return []
            
        data = pd.DataFrame(records)
        
        # Defensive check: ensure 'Group' exists in the sheet
        if 'Group' not in data.columns:
            st.error(f"Spreadsheet Error: Column 'Group' not found. Found: {list(data.columns)}")
            return []
            
        filtered_data = data[data['Group'] == group_name]
        return filtered_data.to_dict('records')
    except Exception as e:
        st.error(f"Error fetching materials: {e}")
        return []
        
