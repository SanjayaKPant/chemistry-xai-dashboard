import streamlit as st
from database_manager import get_gspread_client, log_temporal_trace
from datetime import datetime

def show_teacher_portal(user):
    st.title(f"👨‍🏫 Teacher Command Center: {user['name']}")
    
    selected_group = st.sidebar.selectbox("Select Target Class Group", ["Exp_A", "Exp_B", "Control"])
    
    st.header("📚 Upload Instructional Design")
    
    with st.form("publish_form", clear_on_submit=True):
        title = st.text_input("Lesson Title (e.g., Chemical Bonding)")
        mode = st.radio("Instructional Path", ["Traditional (Control)", "AI-Integrated (Experimental)"])
        
        # --- PDF UPLOAD FIELD ---
        uploaded_pdf = st.file_uploader("Upload Lesson PDF", type=['pdf'])
        
        desc = st.text_area("Learning Objectives & Instructions")
        
        submit = st.form_submit_button("🚀 Publish to Student Dashboards")
        
        if submit:
            if title and uploaded_pdf:
                # 1. In a real-world PhD app, you'd upload this to Google Drive here.
                # 2. For now, we will simulate the link to keep your code running.
                placeholder_link = f"Uploaded_File_{uploaded_pdf.name}"
                
                save_material(user['id'], selected_group, title, mode, placeholder_link, desc, "")
                log_temporal_trace(user['id'], f"Uploaded PDF: {title} for {selected_group}")
                st.success(f"PDF '{uploaded_pdf.name}' published to {selected_group}!")
            else:
                st.error("Please provide both a Title and a PDF file.")

def save_material(tid, group, title, mode, link, desc, hint):
    client = get_gspread_client()
    if client:
        try:
            sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60" #
            sh = client.open_by_key(sheet_id)
            worksheet = sh.worksheet("Instructional_Materials")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, tid, group, title, mode, link, desc, hint])
        except Exception as e:
            st.error(f"Error saving to Google Sheets: {e}")
