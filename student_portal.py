import streamlit as st
import pandas as pd
from database_manager import get_materials_by_group, log_temporal_trace

def show():
    """Main entry point for the Student Gate."""
    st.header("🧪 Student Learning Portal")
    
    # 1. Verification of Login Status
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("Please log in through the Student Gate to access materials.")
        return

    user_id = st.session_state.user['id']
    user_name = st.session_state.user['name']
    user_group = st.session_state.user['group']
    
    st.info(f"Welcome, **{user_name}**. Viewing materials for: **{user_group}**")

    # 2. Fetch Materials with Robust Error Handling
    # This prevents the 'Group' column error seen in previous logs
    with st.spinner("Fetching your chemistry modules..."):
        materials = get_materials_by_group(user_group)

    if not materials:
        st.write("No instructional materials have been published for your group yet.")
        return

    # 3. Interactive Lesson Display
    st.subheader("📚 Assigned Chemistry Modules")
    
    for item in materials:
        # Use a container for a clean, professional PhD portal look
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {item['Title']}")
                st.write(f"**Description:** {item['Description']}")
                
                # Plan B (AI-Integrated) Vertical Exploration: Show Scaffolded Hints
                if user_group == "Exp_A" and 'Hint' in item and item['Hint']:
                    with st.expander("💡 View AI-Generated Scaffold"):
                        st.info(item['Hint'])
                        # Log when a student specifically engages with the AI scaffold
                        if st.button("Mark Hint as Read", key=f"hint_{item['Title']}"):
                            log_temporal_trace(user_id, f"READ_AI_HINT: {item['Title']}")
            
            with col2:
                # Vertical Logic: Log the action to the Temporal_Traces sheet
                file_link = item['File_Link']
                st.link_button("📂 View PDF", file_link)
                
                # Because link_buttons redirect, we log the intent to view
                # To capture the data for your thesis
                if st.button("Log Access", key=f"log_{item['Title']}"):
                    log_temporal_trace(user_id, f"ACCESSED_MATERIAL: {item['Title']}")
                    st.toast("Access logged for research data.")

    # 4. Post-Session Assessment (Vertical Growth)
    st.divider()
    if st.button("🏁 Complete Study Session"):
        log_temporal_trace(user_id, "COMPLETED_SESSION")
        st.success("Your study session progress has been recorded.")
