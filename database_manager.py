import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# --- AUTHENTICATION & CLIENT ---
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

# --- CORE LOGIN FUNCTION (Fixes your Log In Error) ---
def check_login(user_id):
    """Checks the 'Participants' sheet for the provided ID."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Participants")
        df = pd.DataFrame(ws.get_all_records())
        
        # Normalize IDs to uppercase for matching
        df['User_ID'] = df['User_ID'].astype(str).str.strip().str.upper()
        match = df[df['User_ID'] == str(user_id).strip().upper()]
        
        if not match.empty:
            return match.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Login Database Error: {e}")
        return None

# --- PhD RESEARCH LOGGERS (12 COLUMNS) ---
def log_assessment(user_id, group, module_id, t1, t2, t3, t4, status, timestamp, t5="", t6="", res="Pending", tag="None"):
    """Logs the 6-Tier journey: Timestamps, User_ID, Group, Module_ID, T1-T4, T5-T6, Result, Tag"""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assessment_Logs")
        row = [timestamp, user_id, group, module_id, t1, t2, t3, t4, t5, t6, res, tag]
        ws.append_row(row)
        return True
    except: return False

def log_temporal_trace(user_id, event_type, details):
    """Logs AI-Student dialogue for qualitative analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, event_type, details])
        return True
    except: return False

# --- TEACHER TOOLS ---
def upload_to_drive(uploaded_file):
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': uploaded_file.name, 'parents': ['YOUR_FOLDER_ID']} # Replace with actual Folder ID
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')
    except: return None

def save_bulk_concepts(teacher_id, group, main_title, data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        row = [datetime.now().strftime("%Y-%m-%d"), teacher_id, group, main_title,
               data['sub_title'], data['objectives'], data['file_link'], data['video_link'],
               data['q_text'], data['oa'], data['ob'], data['oc'], data['od'], data['correct'], data['socratic_tree']]
        ws.append_row(row)
        return True
    except: return False
