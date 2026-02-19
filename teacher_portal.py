import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database_manager import get_gspread_client, save_bulk_concepts

def show():
    st.title("🧪 Research Orchestration Dashboard")
    st.caption("Strategic Tool for Technology-Integrated Science Learning (Grade 10 Chemistry)")

    # High-impact journals require focusing on analytics and design
    tabs = st.tabs(["🏗️ Module Architect", "📊 Learning Analytics", "🧩 Participant Tracking"])

    # --- TAB 1: MODULE ARCHITECT (Designing the Socratic Tree) ---
    with tabs[0]:
        render_module_architect()

    # --- TAB 2: LEARNING ANALYTICS (Real-time Research Data) ---
    with tabs[1]:
        render_research_analytics()

    # --- TAB 3: PARTICIPANT TRACKING ---
    with tabs[2]:
        render_participant_management()

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
        # RESEARCH CORE: The Socratic Logic Column
        tree_logic = st.text_area("Socratic_Tress (AI Logic Script)", 
                                 placeholder="Example: If student fails to mention Atomic Number, ask about Moseley's discovery.")
        
        q_data = st.text_area("Four-Tier Diagnostic Data (Question + Options A,B,C,D)")
        vids = st.text_input("Video Links (One per line)")

        if st.form_submit_button("Deploy to Research Database"):
            if not main_title or not sub_title:
                st.error("Missing critical research fields.")
            else:
                # Format exactly as needed for your spreadsheet columns
                concepts_list = [{
                    "sub_title": sub_title,
                    "outcomes": learning_outcomes,
                    "video_links": vids,
                    "tree_logic": tree_logic,
                    "q_data": q_data
                }]
                success = save_bulk_concepts(main_title, learning_outcomes, group_id, concepts_list)
                if success:
                    st.success(f"Successfully deployed '{sub_title}' for {group_id}!")

def render_research_analytics():
    st.subheader("📊 Cognitive Trajectory Monitor")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        log_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if not log_df.empty:
            # 1. VISUALIZATION: Confidence-Accuracy Correlation (High rank journal requirement)
            st.markdown("#### Student Confidence vs. Accuracy (Tier 2 Analysis)")
            conf_map = {"Unsure": 1, "Sure": 2, "Very Sure": 3}
            log_df['Confidence_Score'] = log_df['Tier_2_Confidence'].map(conf_map)
            
            fig = px.scatter(log_df, x="Sub-Title", y="Confidence_Score", color="Group",
                             title="Confidence Distribution across Chemistry Concepts")
            st.plotly_chart(fig, use_container_width=True)

            # 2. QUALITATIVE DATA: Tier 3 Justifications for XAI Analysis
            st.markdown("#### Qualitative Reasoning Log (Tier 3)")
            st.dataframe(log_df[['User_ID', 'Sub-Title', 'Tier_3_Justification', 'Timestamp']], use_container_width=True)
        else:
            st.warning("Awaiting research data from student participants.")
    except Exception as e:
        st.error(f"Analytics Sync Error: {e}")

def render_participant_management():
    st.subheader("👥 Participant Distribution")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        st.write(f"Active Participants: {len(df)}")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Sync Error: {e}")
