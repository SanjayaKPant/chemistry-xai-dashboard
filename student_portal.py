import streamlit as st
from database_manager import get_materials_by_group

def show():
    st.title("🧪 Student Learning Portal")
    user_group = st.session_state.user['group']
    st.info(f"Welcome, {st.session_state.user['name']}. Accessing materials for: **{user_group}**")

    materials = get_materials_by_group(user_group)

    if not materials:
        st.warning("No materials have been published for your group yet.")
    else:
        for item in materials:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(item['Title'])
                    st.caption(f"Published on: {item['Timestamp']}")
                    st.write(item['Description'])
                with col2:
                    # Direct link to the PDF in the Shared Drive
                    st.link_button("📂 View PDF", item['File_Link'])
