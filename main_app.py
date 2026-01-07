import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.title("🇳🇵 Research Database Connection Test")

# 1. Establish Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Test Writing Data
st.header("Step 1: Write to Database")
test_id = st.text_input("Enter a Test Student ID (e.g., TEST_001):")

if st.button("Send Test Data"):
    if test_id:
        # Create a new row of data
        new_data = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Student_ID": test_id,
            "Group": "Pilot_Test",
            "School": "VPS_Lab",
            "Tier_1_Ans": "Connection Successful",
            "Tier_2_Conf": 100,
            "Tier_3_Reason": "System Test",
            "Tier_4_ReasonConf": 100
        }])

        # Pull existing data and append
        existing_data = conn.read(worksheet="Responses")
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # Update the Google Sheet
        conn.update(worksheet="Responses", data=updated_df)
        st.success(f"Successfully recorded {test_id} in Google Sheets!")
    else:
        st.error("Please enter an ID first.")

# 3. Test Reading Data
st.divider()
st.header("Step 2: Read from Database")
if st.button("Refresh Data View"):
    df = conn.read(worksheet="Responses")
    st.dataframe(df)
