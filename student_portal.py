import streamlit as st
from database_manager import get_materials_by_group, log_temporal_trace

def show():
    st.header("🧪 Student Learning Portal")
    
    # 1. Verification of Session State
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("Please log in to access your research materials.")
        return

    user_id = st.session_state.user['id']
    user_group = st.session_state.user['group']
    
    st.info(f"Welcome, **{st.session_state.user['name']}**. Accessing modules for: **{user_group}**")

    # 2. Vertical Exploration: Fetch and Filter Data
    # This specifically addresses the 'Group' header error by using the robust fetcher
    materials = get_materials_by_group(user_group)

    if not materials:
        st.write("No materials have been published for your group yet.")
        return

    # 3. Interactive Display & Research Logging
    for item in materials:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(item['Title'])
                st.write(item['Description'])
                # Plan B (Experimental) only: Show AI Scaffolding Hint
                if user_group == "Exp_A" and item.get('Hint'):
                    with st.expander("💡 View AI Scaffolding Hint"):
                        st.write(item['Hint'])
            
            with col2:
                # Vertical Logic: When clicked, it logs the action BEFORE opening the link
                if st.link_button("📂 Open Material", item['File_Link']):
                    log_temporal_trace(user_id, f"OPENED_FILE: {item['Title']}")

    st.divider()
    st.caption("PhD Research System: All interactions are logged for instructional fidelity.")
