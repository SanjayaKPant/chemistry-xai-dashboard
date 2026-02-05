import streamlit as st
from database_manager import get_materials_by_group

def show():
    st.title("🧪 Student Learning Portal")
    
    # 1. Verify the student is logged in
    if not st.session_state.user:
        st.warning("Please login through the Student Gate first.")
        return

    user_name = st.session_state.user['name']
    user_group = st.session_state.user['group'] # e.g., 'Exp_A' or 'Control'

    st.markdown(f"### Welcome back, **{user_name}**!")
    st.info(f"📍 Currently viewing materials for group: **{user_group}**")

    # 2. Fetch materials from GSheets & Drive based on the student's group
    with st.spinner("Loading your chemistry modules..."):
        materials = get_materials_by_group(user_group)

    # 3. Display the materials
    if not materials:
        st.warning("No instructional materials have been published for your group yet. Please check back later.")
    else:
        st.write(f"You have **{len(materials)}** modules available:")
        
        for item in materials:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"📘 {item['Title']}")
                    st.write(f"**Description:** {item['Description']}")
                    if item.get('Hint'): # Only shows if the teacher provided a hint
                        st.caption(f"💡 AI Scaffold/Hint: {item['Hint']}")
                
                with col2:
                    # This link opens the PDF directly from your Shared Drive 0AJAe9AoSTt6-Uk9PVA
                    st.link_button("📖 View Material", item['File_Link'])
