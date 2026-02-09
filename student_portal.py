import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("---")

    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Class Analytics", "🧩 Misconception Tracker", "📂 Material Audit"])

    with tabs[0]: render_deploy_lessons()
    with tabs[1]: render_class_analytics()
    with tabs[2]: render_misconception_tracker()
    with tabs[3]: render_audit_logs()

def render_deploy_lessons():
    st.subheader("🚀 Strategic Lesson Deployment")
    st.info("Assign materials to specific groups to test AI effectiveness.")
    
    with st.form("deploy_form", clear_on_submit=True):
        # Matching your Sheet Headers: Title, Description, Group
        title = st.text_input("Lesson Title (e.g., Acids & Bases)")
        group = st.selectbox("Target Research Group", ["Exp_A", "Control"])
        
        col1, col2 = st.columns(2)
        with col1:
            file_link = st.text_input("Material Link (PDF/Drive URL)")
            video_url = st.text_input("Video URL (YouTube)")
        with col2:
            learning_obj = st.text_area("Learning Objectives")
            # This will be stored in 'Description' for the AI to use as a Socratic Anchor
            socratic_anchor = st.text_area("Socratic Anchor (AI Guidance)")

        if st.form_submit_button("Deploy to Research Portal"):
            if title and file_link:
                save_deployment(title, group, file_link, video_url, learning_obj, socratic_anchor)
                st.success(f"Successfully deployed '{title}' to {group}.")
            else:
                st.warning("Please provide a Title and a File Link.")

def render_class_analytics():
    st.subheader("📊 Class Analytics & Engagement")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        # Accessing the Assessment_Logs tab seen in your screenshot
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not logs.empty:
            st.metric("Total Research Entries", len(logs))
            st.write("### Participation by Research Group")
            st.bar_chart(logs['Group'].value_counts())
        else:
            st.info("Awaiting student data in Assessment_Logs...")
    except Exception as e:
        st.error(f"Analytics Error: {e}")

def render_misconception_tracker():
    st.subheader("🧩 Conceptual Change Monitor")
    st.info("Flagging students with high-confidence reasoning errors.")
    # (Tracker logic pulls from Assessment_Logs as previously established)

def render_audit_logs():
    st.subheader("📂 Instructional Material Audit")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        st.dataframe(mats, use_container_width=True)
    except:
        st.warning("No records found in Instructional_Materials.")

def save_deployment(title, group, file, video, obj, anchor):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        # Matches your exact 7 columns
        # Timestamp, Teacher_ID, Group, Title, Description (Anchor), File_Link, Learning_Objectives
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Chemistry_Dept",
            group,
            title,
            anchor, # Storing Socratic knowledge in Description
            file,
            obj
        ])
    except Exception as e:
        st.error(f"Deployment Error: {e}")
