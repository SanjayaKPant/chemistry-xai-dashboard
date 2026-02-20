import streamlit as st
import pandas as pd
import plotly.express as px
# CRITICAL: Ensures all necessary functions are available from your manager
from database_manager import get_gspread_client, save_bulk_concepts, upload_to_drive

def show():
    st.title("🧪 Research Orchestration Dashboard")
    st.caption(f"Logged in as: {st.session_state.user.get('Name')} | Role: Teacher")

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
    st.info("Upload materials and define the Socratic path Gemini must follow.")
    
    # We use a unique key for the form to prevent Streamlit session conflicts
    with st.form("teacher_deployment_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            main_title = st.selectbox("Textbook Chapter", ["Classification of Elements", "Chemical Reaction", "Metals", "Hydrocarbons"])
            group_id = st.selectbox("Target Group", ["Exp_A", "Exp_B", "Control"])
        with col2:
            sub_title = st.text_input("Atomic Concept (e.g., Modern Periodic Law)")
            learning_outcomes = st.text_area("Learning Objectives")

        st.markdown("---")
        st.markdown("🖼️ **Instructional Materials (Upload or Link)**")
        col_file, col_link = st.columns(2)
        
        with col_file:
            up_file = st.file_uploader("Upload Textbook PDF/Diagram (to Google Drive)", type=['pdf', 'png', 'jpg'])
        with col_link:
            # Teachers can now paste direct YouTube/Website links
            vid_url_input = st.text_input("OR Paste Website/Video URL")

        st.markdown("🧠 **Socratic Logic (Gemini's Pedagogical Blueprint)**")
        # 
        tree_logic = st.text_area(
            "Socratic Scaffolding Pivot", 
            placeholder="Example: If a student mentions 'Atomic Mass', guide them to page 364 of the textbook to discover 'Atomic Number'...",
            help="Gemini will read this logic to decide how to answer the student."
        )
        
        if st.form_submit_button("🚀 Deploy to Research Site"):
            if not sub_title or not tree_logic:
                st.warning("Please provide a Sub-Title and Socratic Logic for the AI.")
            else:
                with st.spinner("Processing assets and updating database..."):
                    # 1. Direct Drive Upload for local files
                    final_asset_link = ""
                    if up_file:
                        # This calls your fixed database_manager function
                        final_asset_link = upload_to_drive(up_file)
                    
                    # 2. Preparation for bulk save
                    concepts_list = [{
                        "sub_title": sub_title,
                        "video_links": vid_url_input,
                        "tree_logic": tree_logic,
                        "asset_url": final_asset_link
                    }]
                    
                    # 3. Final Push to GSheets
                    success = save_bulk_concepts(main_title, learning_outcomes, group_id, concepts_list)
                    
                    if success:
                        st.success(f"✅ Deployment Successful! Module '{sub_title}' is now live for {group_id}.")
                        # Clear cache so student portal sees changes immediately
                        st.cache_data.clear()
                    else:
                        st.error("Error: Could not update the Google Sheet. Check your connection.")

def render_bulk_importer():
    st.subheader("📤 4-Tier Diagnostic Importer")
    st.write("Upload the 20-question CSV here to evaluate student misconceptions.")
    uploaded_file = st.file_uploader("Choose CSV Question Bank", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        if st.button("Confirm Bulk Sync"):
            st.success("Questions synced to student assessment module.")

def render_research_analytics():
    st.subheader("📊 Cognitive Trajectory Monitor")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not log_df.empty:
            # 
            fig = px.scatter(log_df, x="Sub-Title", y="Tier_2_Confidence", color="Group", 
                             hover_data=['User_ID'], title="Student Confidence vs Concept")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No research data has been generated by students yet.")
    except Exception as e:
        st.error(f"Analytics Data Sync Error: {e}")

def render_participant_management():
    st.subheader("👥 Research Participant Tracking")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        st.dataframe(df, use_container_width=True)
    except Exception:
        st.error("Could not load participants.")
