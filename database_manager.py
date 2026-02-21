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

# --- LOGIN ---
def check_login(user_id):
    client = get_gspread_client()
    try:
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        df['User_ID'] = df['User_ID'].astype(str).str.upper()
        match = df[df['User_ID'] == user_id.upper()]
        return match.iloc[0].to_dict() if not match.empty else None
    except: return None

# --- TEACHER: DEPLOY MATERIALS ---
def save_bulk_concepts(teacher_id, group, main_title, data):
    """
    Saves to Instructional_Materials.
    Order: Timestamp, Teacher_ID, Group, Main_Title, Sub_Title, Learning_Objectives, 
    File_Links, Video_Links, Diagnostic_Question, Option_A, Option_B, Option_C, 
    Option_D, Correct_Answer, Socratic_Tree
    """
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            teacher_id,
            group,
            main_title,
            data['sub_title'],
            data['objectives'],
            data['file_link'],
            data['video_link'],
            data['q_text'],
            data['oa'], data['ob'], data['oc'], data['od'],
            data['correct'],
            data['socratic_tree']
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False
# --- STUDENT: LOG 4-TIER RESPONSE ---
def log_assessment(user_id, group, module_id, t1, t2, t3, t4, diag, misc):
    """Matches: Timestamp, User_ID, Module_ID, Tier_1, Tier_2, Tier_3, Tier_4, Diagnostic_Result, Misconception_Tag, Group"""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assessment_Logs")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([ts, user_id, module_id, t1, t2, t3, t4, diag, misc, group])
        return True
    except: return False

# --- DRIVE UPLOAD ---
def upload_to_drive(uploaded_file, folder_id="YOUR_FOLDER_ID"):
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        meta = {'name': uploaded_file.name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
        f = service.files().create(body=meta, media_body=media, fields='id, webViewLink').execute()
        service.permissions().create(fileId=f.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return f.get('webViewLink')
    except: return None

def log_temporal_trace(user_id, event, details=""):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event, details])
    except: pass
