import streamlit as st
from database_manager import get_materials_by_group, log_temporal_trace

def show():
    st.header("🧪 Student Learning Portal")
    
    # Verify session state to prevent AttributeErrors
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("Please log in to access your modules.")
        return

    user_group = st.session_state.user['group']
    user_id = st.session_state.user['id']

    st.info(f"Welcome, {st.session_state.user['name']}. Group: {user_group}")

    # Vertical Exploration: Fetching materials based on Group (Exp_A or Control)
    # This prevents the 'Group' column error by using the database_manager logic
    materials = get_materials_by_group(user_group)

    if not materials:
        st.write("No materials published yet.")
    else:
        for item in materials:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(item['Title'])
                    st.write(item['Description'])
                    # Experimental Logic: Show AI Scaffolds only for Exp_A
                    if user_group == "Exp_A" and item.get('Hint'):
                        with st.expander("💡 View AI Learning Hint"):
                            st.write(item['Hint'])
                with col2:
                    # Professional logging of student interaction
                    if st.link_button("View PDF", item['File_Link']):
                        log_temporal_trace(user_id, f"VIEWED: {item['Title']}")
