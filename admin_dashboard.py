import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import get_gspread_client

def show_admin_portal():
    st.title("📊 Research Control Center")
    try:
        client = get_gspread_client()
        sh = client.open_by_key(st.secrets["private_gsheets_url"])
        
        resp_df = pd.DataFrame(sh.worksheet("Responses").get_all_records())
        trace_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Submissions", len(resp_df))
        with col2:
            if not resp_df.empty:
                avg_score = resp_df['NLP_Score'].mean()
                st.metric("Avg Reasoning Quality", f"{avg_score:.2f}/7")

        if not resp_df.empty:
            st.subheader("Reasoning Scores by Concept")
            fig = px.histogram(resp_df, x="NLP_Score", color="Tier_1", barmode="group")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recent Activity Traces")
        st.dataframe(trace_df.tail(10), use_container_width=True)
    except Exception as e:
        st.warning(f"Dashboard is waiting for data... ({e})")
