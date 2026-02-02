import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import get_gspread_client

def show_admin_portal():
    st.title("📊 Research Command Center")
    st.markdown("Monitor real-time participant engagement and data distribution.")
    
    try:
        # Establish connection using our robust gspread logic
        client = get_gspread_client()
        sh = client.open_by_url(st.secrets["gsheets"]["spreadsheet"])
        
        # Load Data
        resp_df = pd.DataFrame(sh.worksheet("Responses").get_all_records())
        part_df = pd.DataFrame(sh.worksheet("Participants").get_all_records())

        # --- 1. Top Level Metrics ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Recruited", len(part_df))
        with m2:
            st.metric("Submissions", len(resp_df))
        with m3:
            rate = (len(resp_df)/len(part_df)*100) if len(part_df) > 0 else 0
            st.metric("Completion Rate", f"{rate:.1f}%")

        st.divider()

        # --- 2. Visual Analytics ---
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Group Participation")
            if not resp_df.empty:
                # We merge to find out the group of the people who responded
                merged = resp_df.merge(part_df[['User_ID', 'Group']], on='User_ID', how='left')
                fig_pie = px.pie(merged, names='Group', hole=0.4, 
                                 color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Waiting for first submission...")

        with col_b:
            st.subheader("Confidence Trends")
            if not resp_df.empty:
                fig_bar = px.histogram(resp_df, x="Tier_2", 
                                       labels={'Tier_2': 'Confidence Level'},
                                       color_discrete_sequence=['#007bff'])
                st.plotly_chart(fig_bar, use_container_width=True)

        # --- 3. Raw Data Preview ---
        with st.expander("🔍 View Latest Raw Responses"):
            st.table(resp_df.tail(5))

    except Exception as e:
        st.error(f"Dashboard Sync Error: {e}")
