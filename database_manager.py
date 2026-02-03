import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# --- HARDCODED CREDENTIALS TO BYPASS SECRETS BOX ERRORS ---
def get_service_account_info():
    return {
        "type": "service_account",
        "project_id": "chem-xai-project",
        "private_key_id": "09d9edc434243d5f48924e6dfb83331401965d8e",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDhcHL6DXQMvtZE\nEdp+wDqdQhh//mAe+ITZFMBVnhmYiT5Sq0CnWACyRyWKbOcx2y3mAUj7vwDmYBD0\n3KdNyLh2uEzgYFzpo7fU/LLP2O5tb9vBtRH4rZDCCGMEeYjI+LosT0oa0SCobF3P\njmEKQ7ZF9ftysHh0buTYzR0Y2ZsIJJpNLba1jOjPMfLfm3KffTf8mKsI0rncYlqw\npuWJ8GqmK5sRBnNUtE+5DvtakKDFHqi5CiJsHfhDshQZrGJxdfMoQePgcN715bWZ\ksf8ETT8Ix6Jn3WVfX56Tgw0KANPRGf+XpSdiJP3FX+jbnSdEYbxjuz8zFXMJSdL\n6qfnPHa7AgMBAAECggEAaS7PnmZ/gmDZ1MmlsaTb1Dqd9r4HN/wI88XwVSIeXCKQ\rv6S/GEddhCm7daQ6hyS5jEsTbUY5OPmlXCMKMkhc9bam4eqYiJOZ7P9c+eJmwrp\nNBBZEbddhoJmPJS94tLV/k2CTE/Nlnd1L52FHkZoeWzjBGhc0ypYYOUWkd0ZreqR\nb+MeAYcfj+KttTDih8pLb4bCximDX7HDEfzfiTGtLAgQqsBmmHylznjUBfMIJA0s\nIR8HVqmDqaUyjm3Q4BVjx8+FX6qDxSSS+KOEzHYCR2nXbR8g9AydRs2EFTZzxPp9\n1YGKQaxrgMCaI2OoxTGSIHkB3+FZ2ySY/2IRunZTFQKBgQD/goUZxhkDAdf1OJIL\ni9auxZmpsBnauBAUzqr4ZaY0eVqihu/VzY7oSuOFCQZSPcoSpX4Y0KVxK/QVeQBS\nlhpD+BZ0BUKP6HwlTFLB+Mok8RmNdHeUTPNxd7Fom56Em2Ulgn7HtpJqJdR7XdlP\nGNTXIPmS82J2mDInA6dY2BsaZQKBgQDh3ylgvP4Zue0TlaBDWetrmYsT12HeJeX9\nQ8AlCKbOA+H9ZIJhBe+3DHYURQxsDFczdlmP4w3YyGieJUv1noyB/US/p2iImOCT\nyXfSAUuE0q3Z2HC61SqALsGArpbOjG/frgQlXn5l4uKHgF6WhWkV/QWRwSbHj1pO\n7SkdlWCqnwKBgBOxQIbjAKx9qOJKcN8Y8PvZWOV+IA/+Xabs4rpwQyYKMFUUZ0mo\nJRp8IxruviD6iCd1v8kz03xsccxx3fd/gBi69ygL+7xRo7fQMRSoExRTzK9dSZYR\ndDXLjs3MKKR5wYrpitHjnVc3ATBc5FG3TTgjX3jW70DKrBrbqjsrtLMNAoGADVPY\noi+koqn41i3+/dphbMDrlukfijccQfxsawL+rKtH+2ah1s293kQq93k3iWyU/KFg\GYBhQchZe/NhbwXC7qyeENz06xJyNeYuXsLazOSNg4wk4rFPR676lfg3R8q7kyw2\nbGoN9T8U9L/bVPBcSgLbAEWwXxgTURLnWSqGQKsCgYAL32sLF2sXQoYjl1KUZGH9\n/qareoRn5KqmUjhnIGm7o+f4A3qR8C8NbRZA4O08PLRrhpBqladObo7gSnmSysY9\nu4vYn4PWHUXiJYtC35H8TduXufDMYjENJLXnP34x/shKvDhSG8gP/IIK2P+d8+UG\nS8BH4qZqElxTO1JRtdp+/A==\n-----END PRIVATE KEY-----\n",
        "client_email": "streamlit-research-access@chem-xai-project.iam.gserviceaccount.com",
        "client_id": "116425675333935406982",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-research-access%40chem-xai-project.iam.gserviceaccount.com"
    }

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        creds_info = get_service_account_info()
        # Fix backslashes in the hardcoded key
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Auth failed: {e}")
        return None

def check_login(user_id):
    client = get_gspread_client()
    if not client: return False
    try:
        sheet_url = st.secrets["private_gsheets_url"]
        sh = client.open_by_key(sheet_url)
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        return user_id in data['User_ID'].values.astype(str)
    except Exception as e:
        st.error(f"Login Check Error: {e}")
        return False

# --- PLACEHOLDERS TO STOP THE IMPORTERROR ---
def save_quiz_responses(user_id, responses):
    st.info("Response saving logic will be re-added once login is fixed.")

def save_temporal_traces(user_id, traces):
    pass

def analyze_reasoning_quality(responses):
    return "Analysis engine standby."
