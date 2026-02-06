import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("### Instructional Material Deployment")

    # 1. Initialize session variables to prevent AttributeErrors
    if 'target_group' not in st.session_state:
        st.session_state.target_group = "Exp_A"

    # 2. Database Connection
    client = get_gspread_client()
    if not client:
        st.error("Database connection failed. Please check credentials.")
        return

    sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
    sh = client.open_by_key(sheet_id)
    
    # 3. Form for Uploading Materials (Vertical Depth)
    with st.form("upload_form", clear_on_submit=True):
        st.subheader("Publish New Chemistry Module")
        
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Module Title")
            # Experimental Variable: Target Group
            group = st.selectbox("Assign to Group", ["Control", "Exp_A", "Both"])
        
        with col2:
            file_link = st.text_input("Google Drive PDF Link")
            # Research Mode: Traditional vs AI-Scaffolded
            mode = st.selectbox("Instructional Mode", ["Traditional", "AI-Scaffolded"])

        description = st.text_area("Module Description")
        hint = st.text_area("AI Scaffolding Hint (Leave blank for Control)", help="Only visible to Exp_A")

        submitted = st.form_submit_button("🚀 Publish Module")

        if submitted:
            if title and file_link:
                try:
                    worksheet = sh.worksheet("Instructional_Materials")
                    new_row = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        st.session_state.user['id'],
                        group, # This matches the 'Group' header in your sheet
                        title,
                        description,
                        file_link,
                        mode,
                        hint
                    ]
                    worksheet.append_row(new_row)
                    st.success(f"Successfully published '{title}' to {group} group!")
                except Exception as e:
                    st.error(f"Error updating database: {e}")
            else:
                st.warning("Please provide both a Title and a File Link.")

    # 4. Horizontal Progress: Audit existing materials
    st.divider()
    st.subheader("Published Materials Audit")
    try:
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        if not mats.empty:
            st.dataframe(mats, use_container_width=True)
        else:
            st.info("No materials published yet.")
    except:
        st.write("Awaiting data...")
