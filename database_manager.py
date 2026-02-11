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
    client = get_gspread_client()
    if not client: return None
    try:
        sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants")
        data = pd.DataFrame(worksheet.get_all_records())
        
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

# --- HIERARCHICAL BULK DEPLOYMENT (11 COLUMNS) ---
def save_bulk_concepts(main_title, outcomes, group, concepts_list):
    """
    Saves multiple sub-concepts into the 11-column format.
    Spreadsheet Columns: 
    1. Timestamp, 2. Teacher_ID, 3. Group, 4. Main_Title, 5. Learning_Outcomes, 
    6. Sub_Title, 7. Learning_Objectives, 8. File_Links, 9. Video_Links, 
    10. Socratic_Tree, 11. Four_Tier_Data
    """
    client = get_gspread_client()
    if not client: return False
    try:
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        teacher_id = st.session_state.user['id']

        rows_to_add = []
        for c in concepts_list:
            rows_to_add.append([
                timestamp, 
                teacher_id, 
                group, 
                main_title, 
                outcomes,
                c['sub_title'], 
                c['obj'], 
                c['file_links'], 
                c['video_links'],
                c['tree_logic'], 
                c['q_data']
            ])
        
        ws.append_rows(rows_to_add)
        return True
    except Exception as e:
        st.error(f"Bulk Save Error: {e}")
        return False

# --- 4-TIER STUDENT RESPONSE LOGGING ---
def log_student_response(user_id, sub_title, group, t1, t2, t3, t4):
    """Logs detailed student diagnostics for PhD qualitative/quantitative analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        worksheet = sh.worksheet("Assessment_Logs")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Structure: User_ID, Timestamp, Group, Concept, T1, T2, T3, T4
        new_row = [user_id, timestamp, group, sub_title, t1, t2, t3, t4]
        
        worksheet.append_row(new_row)
        return True
    except Exception as e:
        st.error(f"Logging Error: {e}")
        return False

# --- TEMPORAL TRACE LOGGING ---
def log_temporal_trace(user_id, event_type, details=""):
    """Logs clicks and navigation for time-series engagement analysis."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        worksheet = sh.worksheet("Temporal_Traces")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, user_id, event_type, details])
    except Exception as e:
        print(f"Temporal Log Error: {e}")
