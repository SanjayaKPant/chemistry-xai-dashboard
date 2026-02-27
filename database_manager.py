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

# --- CORE LOGIN (STRIP/UPPER FIX) ---
def check_login(user_id):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        df['User_ID'] = df['User_ID'].astype(str).str.upper().str.strip()
        user_id = str(user_id).upper().strip()
        match = df[df['User_ID'] == user_id]
        return match.iloc[0].to_dict() if not match.empty else None
    except:
        return None

# --- TEACHER & ADMIN TOOLS (RE-INTEGRATED) ---
def upload_to_drive(uploaded_file):
    """Retained from your original code for Teacher assignments."""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': uploaded_file.name, 'parents': ['1pA_yM0eW89P2nBPrK_SPrvA5m_p5zKq_']} 
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')
    except: return None

def save_bulk_concepts(teacher_id, group, main_title, data):
    """Retained for Module deployment."""
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

def save_assignment(teacher_id, group, title, desc, file_url):
    """Retained for homework functionality."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assignments")
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), teacher_id, group, title, desc, file_url])
        return True
    except: return False

# --- STUDENT RESEARCH LOGGING (ENHANCED) ---
def log_assessment(uid, group, module_id, t1, t2, t3, t4, status, timestamp):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assessment_Logs")
        
        # Determine correctness for the 'Diagnostic_Result' column
        m_ws = sh.worksheet("Instructional_Materials")
        m_df = pd.DataFrame(m_ws.get_all_records())
        correct_ans = m_df[m_df['Sub_Title'] == module_id]['Correct_Answer'].values[0]
        result = "Correct" if str(t1).strip() == str(correct_ans).strip() else "Incorrect"

        row = [timestamp, str(uid).upper(), group, module_id, t1, t2, t3, t4, status, result]
        ws.append_row(row)
        return True
    except: return False

def log_temporal_trace(uid, event, details):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(uid).upper(), event, details])
    except: pass
