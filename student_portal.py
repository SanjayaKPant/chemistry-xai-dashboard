def render_learning_path(school):
    st.subheader("📚 Digital Learning Library")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        ws = sh.worksheet("Instructional_Materials")
        data = ws.get_all_values()
        
        if len(data) < 2:
            st.info("No lessons have been deployed yet.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # FIX: Normalize column names to avoid Case-Sensitivity issues
        df.columns = [c.strip().upper() for c in df.columns]
        
        # FIX: Normalize the filter
        target_school = str(school).strip().upper()
        my_data = df[df['GROUP'].str.strip().str.upper() == target_school]

        if my_data.empty:
            st.warning(f"No modules found for {school}. (Searched for: {target_school})")
            return

        for idx, row in my_data.iterrows():
            with st.expander(f"🔹 {row.get('SUB_TITLE', 'Concept')}", expanded=True):
                # UI Component: Learning Resources (Top)
                st.info(f"🎯 **Objectives:** {row.get('LEARNING_OBJECTIVES', 'N/A')}")
                
                c1, c2 = st.columns(2)
                with c1:
                    if row.get('FILE_LINKS'): 
                        st.link_button("📄 Open PDF/Image", row['FILE_LINKS'], use_container_width=True)
                with c2:
                    if row.get('VIDEO_LINKS'): 
                        st.link_button("🎥 Watch Video", row['VIDEO_LINKS'], use_container_width=True)
                
                st.markdown("---")
                
                # 4-Tier Assessment
                st.markdown(f"#### ❓ {row.get('DIAGNOSTIC_QUESTION', 'Question missing')}")
                # ... [Rest of the form code]
