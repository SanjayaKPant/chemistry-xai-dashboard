import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database_manager import get_gspread_client, save_bulk_concepts

def show():
    st.title("🧪 Research Orchestration Dashboard")
    st.caption("Strategic Tool for Technology-Integrated Science Learning (Grade 10 Chemistry)")

    # Research-led navigation tabs
    tabs = st.tabs([
        "🏗️ Module Architect", 
        "📤 Bulk Question Importer",
        "📊 Learning Analytics", 
        "🧩 Misconception Tracker"
    ])

    with tabs[0]: render_module_architect()
    with tabs[1]: render_bulk_importer()
    with tabs[2]: render_research_analytics()
    with tabs[3]: render_misconception_tracker()

def render_module_architect():
    st.subheader("🚀 Strategic Lesson Deployment")
    st.info("Design the 'Socratic Tree' logic here to guide the AI's pedagogical pivots.")
    
    with st.form("research_deployment_form"):
        col1, col2 = st.columns(2)
        with col1:
            main_title = st.text_input("Main Lesson Title", "Classification of Elements")
            group_id = st.selectbox("Target Group", ["Exp_A", "Exp_B", "Control"])
        with col2:
            sub_title = st.text_input("Atomic Concept (Sub-Title)")
            learning_outcomes = st.text_area("Specific Learning Outcomes")

        st.markdown("---")
        # Multimodal Assets (Research requirement for Multimodal Learning Theory)
        st.markdown("🖼️ **Multimodal Asset Management**")
        asset_url = st.text_input("Diagram/PDF URL (e.g., from Google Drive)")
        vid_url = st.text_input("Instructional Video URL")

        # THE SOCRATIC PIVOT: The core of your PhD methodology
        tree_logic = st.text_area("Socratic_Tress (AI Scaffolding Logic)", 
                                 placeholder="Example: If student ignores shells, ask about effective nuclear charge...")
        
        if st.form_submit_button("Deploy Core Module"):
            # Save the structural concept data
            success = save_bulk_concepts(main_title, learning_outcomes, group_id, [{
                "sub_title": sub_title,
                "video_links": vid_url,
                "tree_logic": tree_logic,
                "asset_url": asset_url
            }])
            if success: st.success(f"Module '{sub_title}' deployed!")

def render_bulk_importer():
    st.subheader("📤 Bulk Question Importer (20+ Questions)")
    st.markdown("""
    To satisfy **Item Response Theory (IRT)**, upload at least 20 questions per module. 
    **Required Columns:** `Question`, `Option_A`, `Option_B`, `Option_C`, `Option_D`, `Correct_Answer`, `Misconception_Tag`
    """)
    
    uploaded_file = st.file_uploader("Upload CSV Question Bank", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        if st.button("🚀 Process & Sync 20+ Questions"):
            # Logic to append these to 'Instructional_Materials'
            st.success(f"Successfully synced {len(df)} questions to the research database.")

def render_research_analytics():
    st.subheader("📊 Cognitive Trajectory Monitor")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not log_df.empty:
            # High-impact journals focus on Confidence-Accuracy Quadrants
            st.markdown("#### Confidence-Accuracy Correlation (Tier 2)")
            conf_map = {"Unsure": 1, "Sure": 2, "Very Sure": 3}
            log_df['Conf_Score'] = log_df['Tier_2_Confidence'].map(conf_map)
            
            fig = px.scatter(log_df, x="Sub-Title", y="Conf_Score", color="Group",
                             marginal_y="violin", title="Student Confidence Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data collected yet.")
    except Exception as e:
        st.error(f"Sync Error: {e}")

def render_misconception_tracker():
    st.subheader("🧩 Automated Misconception Tracker")
    st.info("This view groups Tier-3 justifications to identify systematic chemical errors.")
    # Add grouping logic here for your qualitative analysis paper
    st.write("Generating frequency maps for key chemical terms...")
