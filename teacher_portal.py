import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import get_gspread_client, save_bulk_concepts

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    st.markdown("---")

    tabs = st.tabs(["🚀 Deploy Lessons", "📊 Class Analytics", "🧩 Misconception Tracker", "📂 Material Audit"])

    with tabs[0]: render_deploy_lessons()
    with tabs[1]: st.info("Analytics dashboard is being updated for hierarchical data...")
    with tabs[2]: st.info("Misconception tracker is being updated for 4-tier analysis...")
    with tabs[3]: render_audit_logs()

def render_deploy_lessons():
    st.subheader("🚀 Strategic Lesson Deployment")
    st.caption("Organize your lesson into 'Atomic Concepts' (Up to 50) for precise diagnostic tracking.")
    
    # Global Lesson Settings
    col1, col2 = st.columns(2)
    with col1:
        main_title = st.text_input("Main Lesson Title", "Acid, Base, and Salt")
    with col2:
        group_id = st.selectbox("Target Research Group", ["Exp_A", "Control"])
    
    outcomes = st.text_area("Global Learning Outcomes (Big Picture Goals)")

    st.markdown("---")
    
    # Manage sub-concept count in session state
    if 'concept_count' not in st.session_state:
        st.session_state.concept_count = 1

    concepts_list = []
    
    with st.form("multi_concept_form", clear_on_submit=True):
        for i in range(st.session_state.concept_count):
            with st.container(border=True):
                st.markdown(f"#### 📍 Sub-Concept #{i+1}")
                sub_title = st.text_input("Sub-title (e.g., Arrhenius Theory)", key=f"sub_{i}")
                obj = st.text_area("Learning Objectives (Specific)", key=f"obj_{i}")
                
                # Media
                vids = st.text_area("Video Links (One URL per line)", key=f"vid_{i}")
                
                # Experimental Logic
                tree = ""
                if group_id == "Exp_A":
                    tree = st.text_area("Socratic Tree (IF: misconception | THEN: pivot)", key=f"tree_{i}", 
                                        help="Example: IF: acids are liquids | THEN: What about solid citric acid?")
                
                # Diagnostic Data
                q_data = st.text_area("Four-Tier Question Data", key=f"q_{i}", 
                                      help="Type your question and options here. This will show on the student's dashboard.")
                
                concepts_list.append({
                    "sub_title": sub_title,
                    "obj": obj,
                    "video_links": vids,
                    "tree_logic": tree,
                    "q_data": q_data,
                    "file_links": "N/A" # Placeholder for drive integration
                })

        submit = st.form_submit_button("🚀 Deploy Full Architecture to Research Database")
        
        if submit:
            if not main_title or not concepts_list[0]['sub_title']:
                st.error("Please provide at least a Main Title and one Sub-title.")
            else:
                success = save_bulk_concepts(main_title, outcomes, group_id, concepts_list)
                if success:
                    st.success(f"Successfully deployed '{main_title}' with {len(concepts_list)} concepts to {group_id}!")
                    st.session_state.concept_count = 1 # Reset after success
                else:
                    st.error("Database connection failed. Please check your Sheet headers.")

    # Add Concept Button (outside the form)
    if st.button("➕ Add Another Sub-title (Concept)"):
        st.session_state.concept_count += 1
        st.rerun()

def render_audit_logs():
    st.subheader("📂 Instructional Materials Audit")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        worksheet = sh.worksheet("Instructional_Materials")
        data = pd.DataFrame(worksheet.get_all_records())
        st.dataframe(data)
    except Exception as e:
        st.warning(f"Could not load audit logs: {e}")
