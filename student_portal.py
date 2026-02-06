import streamlit as st
from database_manager import get_materials_by_group, log_temporal_trace

def show():
    st.header("🧪 Student Learning Portal")
    user = st.session_state.user
    
    st.info(f"Welcome, {user['name']} (Group: {user['group']})")

    # Robust fetching to prevent the 'Group' column error
    materials = get_materials_by_group(user['group'])

    if not materials:
        st.warning("No lessons have been published for your group yet.")
        return

    for item in materials:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(item['Title'])
                st.write(item['Description'])
                
                # Experimental Variable: AI Scaffolding
                if user['group'] == "Exp_A" and item.get('Hint'):
                    with st.expander("💡 AI Learning Scaffold"):
                        st.info(item['Hint'])
                        if st.button("Mark Hint as Read", key=f"hint_{item['Title']}"):
                            log_temporal_trace(user['id'], f"READ_HINT: {item['Title']}")

            with col2:
                # Direct Link to Shared Drive 0AJAe9AoSTt6-Uk9PVA
                st.link_button("📂 View PDF", item['File_Link'])
                if st.button("Log Access", key=f"log_{item['Title']}"):
                    log_temporal_trace(user['id'], f"ACCESSED: {item['Title']}")
                    st.toast("Progress Saved!")
