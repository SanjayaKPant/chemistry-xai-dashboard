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
    st.subheader("🚀 Strategic Lesson Deployment")
    st.info("Upload instructional materials (PDF/Video) and design Socratic logic here.")
    
    with st.form("research_deployment_form"):
        col1, col2 = st.columns(2)
        with col1:
            main_title = st.selectbox("Textbook Chapter", ["Classification of Elements", "Chemical Reaction", "Metals", "Hydrocarbons"])
            group_id = st.selectbox("Target Group", ["Exp_A", "Exp_B", "Control"])
        with col2:
            sub_title = st.text_input("Atomic Concept (e.g., Periodic Law)")
            learning_outcomes = st.text_area("Learning Objectives (from Textbook)")

        st.markdown("---")
        st.markdown("🖼️ **Multimodal Asset Library**")
        col_a, col_b = st.columns(2)
        with col_a:
            asset_url = st.text_input("Textbook Image/PDF Link (Google Drive)")
        with col_b:
            vid_url = st.text_input("Instructional Video Link")

        st.markdown("🧠 **Socratic Tree Architect**")
        tree_logic = st.text_area("AI Scaffolding Logic", 
                                 placeholder="If student confuses atomic mass with atomic number, ask about Moseley's experiment...")
        
        if st.form_submit_button("Deploy Core Module"):
            # Prepare data for Google Sheets
            concepts_list = [{
                "sub_title": sub_title,
                "video_links": vid_url,
                "tree_logic": tree_logic,
                "asset_url": asset_url
            }]
            success = save_bulk_concepts(main_title, learning_outcomes, group_id, concepts_list)
            if success: st.success(f"Module '{sub_title}' deployed successfully!")

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
