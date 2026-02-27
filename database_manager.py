import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# --- 1. AUTHENTICATION & CONNECTION ---
def get_creds():
    """VPS Secure Auth: Handles GCP Service Account and Private Key formatting."""
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

# --- 2. CORE LOGIN ---
def check_login(user_id):
    """Verifies User_ID and retrieves role/group from Participants sheet."""
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

# --- 3. TEACHER & ADMIN TOOLS ---
def upload_to_drive(uploaded_file):
    """
    Fixed Drive Upload: Resolves previous SyntaxError.
    Uploads supplementary materials to a centralized PhD research folder.
    """
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {
            'name': uploaded_file.name, 
            'parents': ['1pA_yM0eW89P2nBPrK_SPrvA5m_p5zKq_']
        } 
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
        
        # CORRECTED SYNTAX: No nested assignments
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Drive Error: {e}")
        return None

def save_bulk_concepts(teacher_id, group, main_title, data):
    """Logs instructional content including diagnostic questions and Socratic trees."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        row = [
            datetime.now().strftime("%Y-%m-%d"), teacher_id, group, main_title,
            data['sub_title'], data['objectives'], data['file_link'], data['video_link'],
            data['q_text'], data['oa'], data['ob'], data['oc'], data['od'], data['correct'], data['socratic_tree']
        ]
        ws.append_row(row)
        return True
    except: return False

def save_assignment(teacher_id, group, title, desc, file_url):
    """Records homework assignments for specific research cohorts."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assignments")
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), teacher_id, group, title, desc, file_url])
        return True
    except: return False

# --- 4. PhD RESEARCH LOGGING (TIERS 1-6) ---
def log_assessment(uid, group, module_id, t1, t2, t3, t4, status, timestamp, t5="N/A", t6="N/A"):
    """
    The 6-Tier Engine: Tracks the evolution of a student's mental model.
    T1-T4: Initial mindset.
    T5-T6: Post-Socratic Revision.
    """
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Assessment_Logs")
        
        m_ws = sh.worksheet("Instructional_Materials")
        m_df = pd.DataFrame(m_ws.get_all_records())
        correct_ans = m_df[m_df['Sub_Title'] == module_id]['Correct_Answer'].values[0]
        
        # Mastery logic for data analysis
        check_val = t5 if status == "POST" else t1
        result = "Correct" if str(check_val).strip() == str(correct_ans).strip() else "Incorrect"

        row = [timestamp, str(uid).upper(), group, module_id, t1, t2, t3, t4, status, result, t5, t6]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Logging Error: {e}")
        return False

def log_temporal_trace(uid, event, details):
    """Stores micro-genetic traces for learning curve analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Temporal_Traces")
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(uid).upper(), event, details])
    except: pass

def fetch_chat_history(uid, module_id):
    """Enables Socratic continuity by reloading previous chat interactions."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
        if df.empty: return []
        
        mask = (df['User_ID'].astype(str).str.upper() == uid.upper()) & \
               (df['Event'] == "CHAT_MSG") & \
               (df['Details'].str.contains(module_id))
        filtered = df[mask]
        
        history = []
        for _, row in filtered.iterrows():
            content = row['Details'].split("| Content: ")[-1] if "| Content: " in row['Details'] else row['Details']
            history.append({"role": "user", "content": content})
        return history
    except: return []
