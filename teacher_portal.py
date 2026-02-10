import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Analytics", "🧩 Tracker", "📂 Audit"])
    with tabs[0]: render_deploy_lessons()
    with tabs[1]: st.info("Analytics coming soon...")
    with tabs[2]: st.info("Tracker coming soon...")
    with tabs[3]: render_audit_logs()

def render_deploy_lessons():
    st.subheader("🚀 Hierarchical Lesson Deployment")
    
    # Global Settings
    col_a, col_b = st.columns(2)
    with col_a:
        main_title = st.text_input("Main Lesson Title", placeholder="e.g., Acids, Bases, and Salts")
    with col_b:
        target_group = st.selectbox("Research Group", ["Exp_A", "Control"])
    
    learning_outcomes = st.text_area("Global Learning Outcomes (Key Takeaways)")

    st.markdown("---")
    st.write("### 🧩 Concept Breakdown (Sub-titles)")
    
    if 'concept_count' not in st.session_state:
        st.session_state.concept_count = 1

    concepts_data = []
    
    # Form handles the bulk submission
    with st.form("multi_concept_form"):
        for i in range(st.session_state.concept_count):
            with st.container(border=True):
                st.markdown(f"#### 📍 Sub-Concept #{i+1}")
                sub_title = st.text_input("Sub-title", key=f"sub_{i}", placeholder="e.g., Arrhenius Concept")
                sub_obj = st.text_area("Learning Objectives", key=f"obj_{i}")
                
                # Media Section
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    files = st.file_uploader("Upload Images/PDFs", accept_multiple_files=True, key=f"file_{i}")
                with m_col2:
                    videos = st.text_area("Video Links (One per line)", key=f"vid_{i}")

                # Socratic Logic
                tree = ""
                if target_group == "Exp_A":
                    tree = st.text_area("Socratic Tree (IF: misconception | THEN: pivot)", key=f"tree_{i}")
                
                # 4-Tier Data
                q_data = st.text_area("4-Tier Question (Raw Text)", key=f"q_{i}")
                
                concepts_data.append({
                    "sub_title": sub_title, "obj": sub_obj, "logic": tree, "q": q_data, "vids": videos
                })

        if st.form_submit_button("🚀 Deploy All Concepts"):
            save_bulk_deployment(main_title, learning_outcomes, target_group, concepts_data)
            st.success(f"Deployed {len(concepts_data)} concepts to {target_group}!")

    if st.button("➕ Add Sub-title (Concept)"):
        st.session_state.concept_count += 1
        st.rerun()

def save_bulk_deployment(main, outcomes, group, data_list):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        for concept in data_list:
            ws.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M"), "Admin_Teacher", group, 
                main, outcomes, concept['sub_title'], concept['obj'], 
                "Links_Pending", concept['vids'], concept['logic'], concept['q']
            ])
    except Exception as e: st.error(f"Error: {e}")

def render_audit_logs():
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        st.dataframe(pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records()))
    except: st.warning("No data.")
