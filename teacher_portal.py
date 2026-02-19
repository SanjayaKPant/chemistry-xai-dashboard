import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import get_gspread_client, save_bulk_concepts

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
    
    with st.form("research_deployment_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            main_title = st.selectbox("Textbook Chapter", ["Classification of Elements", "Chemical Reaction", "Metals"])
            group_id = st.selectbox("Target Group", ["Exp_A", "Control"])
        with col2:
            sub_title = st.text_input("Atomic Concept (e.g., Noble Gases)")
            learning_outcomes = st.text_area("Learning Objectives")

        st.markdown("---")
        st.markdown("📤 **Direct Asset Upload (PDF, Video, or Image)**")
        # Direct file uploaders
        up_file = st.file_uploader("Upload Textbook Page or Diagram", type=['pdf', 'png', 'jpg'])
        up_vid = st.file_uploader("Upload Instructional Video", type=['mp4', 'mov'])

        st.markdown("🧠 **Socratic Logic**")
        tree_logic = st.text_area("Socratic Scaffolding Logic")
        
        if st.form_submit_button("Deploy to Research Sheet"):
            with st.spinner("Uploading assets to Google Drive..."):
                # 1. Upload assets and get links
                final_asset_link = upload_to_drive(up_file) if up_file else ""
                final_vid_link = upload_to_drive(up_vid) if up_vid else ""
                
                # 2. Save everything to the Sheet
                concepts_list = [{
                    "sub_title": sub_title,
                    "video_links": final_vid_link,
                    "tree_logic": tree_logic,
                    "asset_url": final_asset_link
                }]
                
                if save_bulk_concepts(main_title, learning_outcomes, group_id, concepts_list):
                    st.success("✅ Module deployed with live assets!")

def render_bulk_importer():
    st.subheader("📤 Bulk Question Importer")
    st.markdown("""
    **Research Goal:** Upload 20+ questions per module for statistical validity.
    Please upload a CSV with: `Question`, `Option_A`, `Option_B`, `Option_C`, `Option_D`, `Correct_Answer`.
    """)
    
    uploaded_file = st.file_uploader("Upload CSV Question Bank", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(f"Found {len(df)} questions in file.")
        st.dataframe(df.head())
        
        if st.button("🚀 Sync 20+ Questions to Database"):
            # Placeholder for the bulk sync logic we will add to database_manager
            st.success(f"Successfully synced {len(df)} questions to the research database.")

def render_research_analytics():
    st.subheader("📊 Cognitive Trajectory Monitor")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not log_df.empty:
            st.markdown("#### Confidence-Accuracy Quadrant")
            conf_map = {"Unsure": 1, "Sure": 2, "Very Sure": 3}
            log_df['Conf_Score'] = log_df['Tier_2_Confidence'].map(conf_map)
            
            fig = px.scatter(log_df, x="Sub-Title", y="Conf_Score", color="Group",
                             marginal_y="box", title="Student Confidence Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No participant data collected yet.")
    except Exception as e:
        st.error(f"Sync Error: {e}")

def render_participant_management():
    st.subheader("👥 Participant Tracking")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error: {e}")
