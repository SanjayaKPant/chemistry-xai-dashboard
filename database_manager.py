def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        
        # --- THIS LINE IS THE FIX ---
        client = gspread.authorize(credentials) 
        # ----------------------------
        
        return client
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None
