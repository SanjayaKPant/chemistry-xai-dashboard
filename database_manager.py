import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# --- AUTHENTICATION ---
def get_creds():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

def get_gspread_client():
    creds = get_creds()
    return gspread.authorize(creds) if creds else None

# --- TEACHER: SAVE MODULES ---
def save_bulk_concepts(teacher_id, group, main_title, data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        
        # Ensure the column names here match your GSheet exactly
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            teacher_id,
            group, # This saves as "Group"
            main_title,
            data.get('sub_title', ''),
            data.get('objectives', ''),
            data.get('file_link', ''),
            data.get('video_link', ''),
            data.get('q_text', ''),
            data.get('oa', ''), 
            data.get('ob', ''), 
            data.get('oc', ''), 
            data.get('od', ''),
            data.get('correct', ''),
            data.get('socratic_tree', '')
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"GSheets Sync Error: {e}")
        return False

# --- DRIVE: UPLOAD ASSETS ---
def upload_to_drive(uploaded_file):
    # Correct ID extracted from your URL
    FOLDER_ID = "0AJAe9AoSTt6-Uk9PVA" 
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': uploaded_file.name,
            'parents': [FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), 
                                  mimetype=uploaded_file.type)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        # Public permission so students can view the PDF/Image
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Drive Error: {e}")
        return ""
