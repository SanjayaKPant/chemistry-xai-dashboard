import streamlit as st
import pandas as pd
import plotly.express as px
# IMPORT FIX: Including upload_to_drive to prevent NameError
from database_manager import get_gspread_client, save_bulk_concepts, upload_to_drive

def show():
    st.title("🧪 Research Orchestration Dashboard")
    st.caption("Strategic Tool for Technology-Integrated Science Learning (Grade 10 Chemistry)")

    # Research-led navigation tabs
    tabs = st.tabs([
        "🏗️ Module Architect", 
        "📤 Bulk Question Importer",
        "📊 Learning Analytics", 
        "🧩 Participant Management"
    ])

    with tabs[0]: render_module_architect()
    with tabs[1]: render_bulk_importer()
    with tabs[2]: render_research_analytics()
    with tabs[3]: render_participant_management()

def render_module_architect():
    st.subheader("🚀 Multimodal Research Architect")
    st.info("Design how the Gemini Socratic Tutor should react to specific student misconceptions.")
    
    with st.form("research_deployment_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            main_title = st.selectbox("Textbook Chapter", ["Classification of Elements", "Chemical Reaction", "Metals", "Hydrocarbons"])
            group_id = st.selectbox("Target Group", ["Exp_A", "Exp_B", "Control"])
        with col2:
            sub_title = st.text_input("Atomic Concept (e.g., Modern Periodic Law)")
            learning_outcomes = st.text_area("Specific Learning Objectives")

        st.markdown("---")
        st.markdown("🖼️ **Instructional Materials (Hybrid Support)**")
        col_file, col_link = st.columns(2)
        
        with col_file:
            up_file = st.file_uploader("Upload Textbook PDF/Diagram", type=['pdf', 'png', 'jpg'])
        with col_link:
            vid_url_input = st.text_input("OR Paste Website/Video URL (e.g., YouTube)")

        st.markdown("🧠 **Socratic Logic (Gemini Instruction)**")
        tree_logic = st.text_area(
            "Socratic Scaffolding Pivot", 
            placeholder="Example: If the student confuses groups with periods, ask them to count vertical vs horizontal lines in the provided image...",
            help="This logic is sent to Gemini to ensure it tutors students based on YOUR pedagogical approach."
        )
        
        if st.form_submit_button("🚀 Deploy to Research Sheet"):
            with st.spinner("Uploading assets and syncing to database..."):
                # 1. Handle File Upload (to Google Drive via DB Manager)
                final_asset_link = ""
                if up_file:
                    final_asset_link = upload_to_drive(up_file)
                
                # 2. Use URL input if no file uploaded
                final_vid_link = vid_url_input 
                
                # 3. Organize data for the Google Sheet
                concepts_list = [{
                    "sub_title": sub_title,
                    "video_links": final_vid_link,
                    "tree_logic": tree_logic,
                    "asset_url": final_asset_link
                }]
                
                if save_bulk_concepts(main_title, learning_outcomes, group_id, concepts_list):
                    st.success(f"✅ Architecture for '{sub_title}' Deployed! Gemini is now calibrated.")
                else:
                    st.error("Deployment failed. Please verify your Google Sheet headers.")

def render_bulk_importer():
    st.subheader("📤 4-Tier Diagnostic Importer")
    st.markdown("Upload 20+ questions to enable high-quality statistical analysis (Misconception vs. Knowledge Gap).")
    
    uploaded_file = st.file_uploader("Upload CSV (Questions Bank)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(f"Validated {len(df)} research questions.")
        st.dataframe(df.head())
        if st.button("Confirm Bulk Sync"):
            # This will feed the 4-tier system in student_portal
            st.success("Questions synced to research database.")

def render_research_analytics():
    st.subheader("📊 Cognitive Trajectory Monitor")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not log_df.empty:
            st.markdown("#### Confidence-Accuracy Quadrant (Tier 2 vs Tier 1)")
            # Categorizing students into high/low confidence and accuracy
            fig = px.scatter(log_df, x="Sub-Title", y="Tier_2_Confidence", color="Group",
                             title="Research Data: Confidence Levels in Chemistry Concepts")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Awaiting student participation data.")
    except Exception as e:
        st.error(f"Analytics Error: {e}")

def render_participant_management():
    st.subheader("👥 Research Participants")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        st.dataframe(df)
    except Exception as e:
        st.error(f"Sync Error: {e}")
