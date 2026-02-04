def check_login(user_id):
    client = get_gspread_client()
    if not client: return None
    try:
        raw_id = st.secrets["general"]["private_gsheets_url"]
        sheet_id = raw_id.split("/d/")[-1].split("/")[0].strip()
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet("Participants") 
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Clean inputs for matching
        data['User_ID'] = data['User_ID'].astype(str).str.strip().str.upper()
        search_id = str(user_id).strip().upper()
        
        user_row = data[data['User_ID'] == search_id]
        
        if not user_row.empty:
            # Return a dictionary of user details
            return {
                "id": user_row.iloc[0]['User_ID'],
                "name": user_row.iloc[0]['Name'],
                "role": user_row.iloc[0]['Role'],
                "group": user_row.iloc[0]['Group']
            }
        return None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None
