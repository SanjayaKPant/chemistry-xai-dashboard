import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
from googleapiclient.http import MediaIoBaseUpload
import io

# --- GOOGLE CLIENTS & AUTH ---
def get_creds():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("GCP Service Account secrets missing!")
            return None
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

# --- CORE LOGIN LOGIC ---
def check_login(user_id):
    client = get_gspread_client()
    if not client: return None
    try:
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        users_df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        # Ensure ID column is treated as string for comparison
        users_df['User_ID'] = users_df['User_ID'].astype(str).str.upper()
        user_match = users_df[users_df['User_ID'] == user_id]
        
        if not user_match.empty:
            return user_match.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

# --- RESEARCH DATA DEPLOYMENT ---
def save_bulk_concepts(main_title, outcomes, group, concept_list):
    """Saves multimodal research modules to Google Sheets."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        
        rows_to_add = []
        for c in concept_list:
            # Matches the columns: Main_Title, Learning_Objectives, Group, Sub-Title, Video_Links, Socratic_Tress, Asset_URL
            rows_to_add.append([
                main_title, 
                outcomes, 
                group, 
                c['sub_title'], 
                c.get('video_links', ""), 
                c.get('tree_logic', ""), 
                c.get('asset_url', "")
            ])
        ws.append_rows(rows_to_add)
        return True
    except Exception as e:
        st.error(f"Bulk Save Error: {e}")
        return False

# --- LOGGING FUNCTIONS ---
def log_student_response(user_id, sub_title, group, t1, t2, t3, t4):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        worksheet = sh.worksheet("Assessment_Logs")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [user_id, timestamp, group, sub_title, t1, t2, t3, t4]
        worksheet.append_row(new_row)
        return True
    except Exception as e:
        st.error(f"Logging Error: {e}")
        return False

def log_temporal_trace(user_id, event_type, details=""):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        worksheet = sh.worksheet("Temporal_Traces")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([user_id, timestamp, event_type, details])
    except Exception as e:
        pass # Silent fail for traces to avoid interrupting user flow


def upload_to_drive(uploaded_file, folder_id="YOUR_DRIVE_FOLDER_ID"):
    """Uploads a file to Google Drive and returns the shareable link."""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': uploaded_file.name,
            'parents': [folder_id]
        }
        
        # Determine MIME type
        media = MediaIoBaseUpload(
            io.BytesIO(uploaded_file.getvalue()), 
            mimetype=uploaded_file.type, 
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        # Set permissions to 'anyone with link can view' for the research app
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Drive Upload Error: {e}")
        return None
