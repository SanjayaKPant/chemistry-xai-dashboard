import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client, log_temporal_trace

def show_teacher_portal(user):
    st.title(f"👨‍🏫 Teacher Command Center: {user['name']}") #
    
    # Selection for personalized targeting
    selected_group = st.sidebar.selectbox("Select Target Class Group", ["Exp_A", "Exp_B", "Control"])
    
    st.header("📚 Personalized Instructional Design")
    
    with st.form("publish_form"):
        title = st.text_input("Lesson Title (e.g., Atomic Theory)")
        mode = st.radio("Instructional Path", ["Traditional (Control)", "AI-Integrated (Experimental)"])
        link = st.text_input("Material URL (Google Drive/PDF)")
        desc = st.text_area("Learning Objectives & Instructions")
        
        # NEW: High-refinement field for AI personalization
        ai_hint = ""
        if mode == "AI-Integrated (Experimental)":
            ai_hint = st.text_input("AI Persona Hint (e.g., 'Focus on Bohr Model misconceptions')")
            
        submit = st.form_submit_button("🚀 Publish to Student Dashboards")
        
        if submit:
            if title and link:
                save_material(user['id'], selected_group, title, mode, link, desc, ai_hint)
                log_temporal_trace(user['id'], f"Published {title} to {selected_group}")
                st.success(f"Successfully published to {selected_group}!")
            else:
                st.error("Please provide both a Title and a Material Link.")

def save_material(tid, group, title, mode, link, desc, hint):
    client = get_gspread_client()
    if client:
        try:
            # Your specific Sheet ID
            sheet_id = "1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60"
            sh = client.open_by_key(sheet_id)
            worksheet = sh.worksheet("Instructional_Materials")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, tid, group, title, mode, link, desc, hint])
        except Exception as e:
            st.error(f"Save Error: {e}. Ensure you created the 'Instructional_Materials' tab.")
