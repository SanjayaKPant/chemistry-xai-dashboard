import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

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

def check_login(user_id):
    client = get_gspread_client()
    try:
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        df['User_ID'] = df['User_ID'].astype(str).str.upper()
        match = df[df['User_ID'] == user_id.upper()]
        return match.iloc[0].to_dict() if not match.empty else None
    except: return None

def save_bulk_concepts(teacher_id, group, main_title, data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        # Ensure the order matches your GSheet columns exactly
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            teacher_id, group, main_title, 
            data.get('sub_title', ''), data.get('objectives', ''),
            data.get('file_link', ''), data.get('video_link', ''),
            data.get('q_text', ''), data.get('oa', ''), data.get('ob', ''), 
            data.get('oc', ''), data.get('od', ''), data.get('correct', ''),
            data.get('socratic_tree', '')
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return False

def upload_to_drive(uploaded_file):
    FOLDER_ID = "0AJAe9AoSTt6-Uk9PVA" 
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        meta = {'name': uploaded_file.name, 'parents': [FOLDER_ID]}
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
        
        # SupportsAllDrives handles the shared folder permission
        f = service.files().create(body=meta, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
        service.permissions().create(fileId=f.get('id'), body={'type': 'anyone', 'role': 'reader'}, supportsAllDrives=True).execute()
        return f.get('webViewLink')
    except Exception as e:
        st.error(f"Drive Error: {e}")
        return ""

def log_assessment(user_id, group, module_id, t1, t2, t3, t4, diag, misc):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assessment_Logs")
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, module_id, t1, t2, t3, t4, diag, misc, group])
        return True
    except: return False

def log_temporal_trace(user_id, event, details=""):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event, details])
    except: pass
