import streamlit as st
from database_manager import get_materials_by_group, log_temporal_trace

def show():
    st.header("📖 Student Learning Portal")
    user = st.session_state.user
    
    # Fetching materials filtered by the student's group
    materials = get_materials_by_group(user['group'])
    
    if not materials:
        # If you see this, check that your 'Group' column in the sheet matches user['group']
        st.info("No lessons have been published for your group yet.")
        return

    for item in materials:
        with st.container(border=True):
            st.subheader(item['Title'])
            st.write(item['Description'])
            
            # Plan B: Show AI Scaffold only to Experimental Group
            if user['group'] == "Exp_A" and 'Hint' in item:
                with st.expander("💡 AI Learning Hint"):
                    st.info(item['Hint'])
            
            # Log access for Temporal Trace research data
            st.link_button("View PDF", item['File_Link'])
            if st.button("Log Access", key=f"log_{item['Title']}"):
                log_temporal_trace(user['id'], f"VIEWED: {item['Title']}")
                st.toast("Access recorded.")
