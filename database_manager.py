def check_login(user_id):
    client = get_gspread_client()
    if not client: return None # Return None if connection fails
    try:
        raw_id = st.secrets["general"]["private_gsheets_url"]
        sheet_id = raw_id.split("/d/")[-1].split("/")[0].strip()
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Look for the user
        user_row = data[data['User_ID'].astype(str).str.strip().str.upper() == str(user_id).strip().upper()]
        
        if not user_row.empty:
            # Return the User_ID and their Role (Student/Teacher/Admin)
            return {"id": user_id, "role": user_row.iloc[0]['Role']}
        return None
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return None
