import streamlit as st
import pandas as pd
from database_manager import get_gspread_client, log_temporal_trace
from datetime import datetime

def show_teacher_portal(user):
    st.title(f"👨‍🏫 Teacher Command Center: {user['name']}")
    st.markdown("---")

    # Sidebar Tools
    st.sidebar.header("Class Management")
    selected_group = st.sidebar.selectbox("Select Class Group", ["Exp_A", "Exp_B", "Control"])

    # 1. INSTRUCTIONAL MATERIAL UPLOAD (Core of Plan A)
    st.header("📚 Instructional Material Management")
    st.write(f"Upload and assign materials for group: **{selected_group}**")
    
    with st.form("upload_form", clear_on_submit=True):
        lesson_title = st.text_input("Lesson Title (e.g., Particulate Nature of Matter)")
        delivery_mode = st.radio("Instructional Type", ["Traditional (Control)", "AI-Integrated (Experimental)"])
        content_link = st.text_input("Link to Material (Google Drive/PDF URL)")
        assignment_desc = st.text_area("Task Description for Students")
        
        submit_update = st.form_submit_button("📢 Publish to Students")
        
        if submit_update:
            # Here we will write to a new 'Assignments' tab in your Google Sheet
            # This triggers the notification for the students
            publish_assignment(user['id'], selected_group, lesson_title, delivery_mode, content_link)
            log_temporal_trace(user['id'], f"Published {lesson_title} to {selected_group}")
            st.success(f"Notification sent to all students in {selected_group}!")

    # 2. RESEARCHER OVERSIGHT AREA
    st.markdown("---")
    st.header("📊 Student Activity Monitor")
    st.write("Real-time view of student logins in your assigned groups.")
    # This provides the "Researcher" perspective you requested
    display_student_activity(selected_group)

def publish_assignment(teacher_id, group, title, mode, link):
    # Logic to append a row to the 'Assignments' tab
    st.info(f"Connecting to Google Sheets to update {group} path...")

def display_student_activity(group):
    # Logic to filter 'Temporal_Traces' for students in this group
    st.caption(f"Displaying trace data for {group}...")
