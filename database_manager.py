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
        st.error(f"Auth Error: {e}")
        return None

def get_gspread_client():
    creds = get_creds()
    return gspread.authorize(creds) if creds else None

# --- DRIVE: UPLOAD (Multiple Files & Shared Drive Support) ---
def upload_to_drive(uploaded_file):
    FOLDER_ID = "0AJAe9AoSTt6-Uk9PVA" 
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        meta = {'name': uploaded_file.name, 'parents': [FOLDER_ID]}
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
        
        f = service.files().create(
            body=meta, 
            media_body=media, 
            fields='id, webViewLink',
            supportsAllDrives=True # Fixed for Shared Drives
        ).execute()
        
        service.permissions().create(
            fileId=f.get('id'), 
            body={'type': 'anyone', 'role': 'reader'},
            supportsAllDrives=True
        ).execute()
        
        return f.get('webViewLink')
    except Exception as e:
        st.error(f"Drive Error: {e}")
        return ""

# --- DATA SAVING ---
def save_bulk_concepts(teacher_id, group, main_title, data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), teacher_id, group, main_title, 
               data.get('sub_title',''), data.get('objectives',''), data.get('file_link',''), 
               data.get('video_link',''), data.get('q_text',''), data.get('oa',''), 
               data.get('ob',''), data.get('oc',''), data.get('od',''), 
               data.get('correct',''), data.get('socratic_tree','')]
        ws.append_row(row)
        return True
    except: return False

def save_assignment(teacher_id, group, title, desc, file_url):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assignments")
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), teacher_id, group, title, desc, file_url])
        return True
    except: return False

def log_temporal_trace(user_id, event, details=""):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event, details])
    except: pass
