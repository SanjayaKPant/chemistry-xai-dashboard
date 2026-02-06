import streamlit as st
from database_manager import get_materials_by_group, log_temporal_trace

def show():
    st.header("🧪 Student Learning Portal")
    user = st.session_state.user
    
    # Vertical Depth: Filtering materials by the student's assigned group
    materials = get_materials_by_group(user['group'])
    
    if not materials:
        st.info("Your teacher hasn't published modules for your group yet.")
        return

    for item in materials:
        with st.container(border=True):
            st.subheader(item['Title'])
            # Plan B: Show AI Scaffold only to Experimental Group
            if user['group'] == "Exp_A":
                with st.expander("💡 AI Learning Hint"):
                    st.write(item.get('Hint', "No hint provided."))
            
            # Log the access for your Temporal Trace data
            if st.link_button("View Material", item['File_Link']):
                log_temporal_trace(user['id'], f"OPENED_{item['Title']}")
