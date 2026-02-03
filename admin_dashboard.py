import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import get_gspread_client

def show_admin_portal():
    st.title("📊 Research Command Center")
    st.markdown("Monitor real-time participant engagement and cognitive load metrics.")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_url(st.secrets["gsheets"]["spreadsheet"])
        
        # Load Dataframes
        resp_df = pd.DataFrame(sh.worksheet("Responses").get_all_records())
        part_df = pd.DataFrame(sh.worksheet("Participants").get_all_records())
        trace_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())

        # --- 1. KEY PERFORMANCE INDICATORS ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Participants", len(part_df))
        with m2:
            st.metric("Total Submissions", len(resp_df))
        with m3:
            # Calculate Average Time-on-Task from Traces
            if not trace_df.empty and 'Details' in trace_df.columns:
                # Extract numbers from "TotalTime:XX.Xs" format
                times = trace_df[trace_df['Event'] == 'SUBMIT_CLICKED']['Details'].str.extract('(\d+\.\d+)').astype(float)
                avg_time = times.mean().iloc[0] if not times.empty else 0
                st.metric("Avg. Time on Task", f"{avg_time:.1f}s")
            else:
                st.metric("Avg. Time on Task", "0s")

        st.divider()

        # --- 2. ANALYTICS GRID ---
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Group Distribution")
            if not resp_df.empty:
                merged = resp_df.merge(part_df[['User_ID', 'Group']], on='User_ID', how='left')
                fig_pie = px.pie(merged, names='Group', hole=0.4, title="Completion by Research Group")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No responses yet.")

        with col_b:
            st.subheader("Confidence Mapping")
            if not resp_df.empty:
                # Comparing Tier 2 (Concept) vs Tier 4 (Reasoning) Confidence
                fig_box = px.box(resp_df, y=["Tier_2", "Tier_4"], title="Confidence Consistency")
                st.plotly_chart(fig_box, use_container_width=True)

        # --- 3. PROCESS MINING PREVIEW ---
        st.subheader("🕵️ Live Process Traces")
        st.write("Recent student interactions (HINTS vs SUBMISSIONS)")
        if not trace_df.empty:
            st.dataframe(trace_df.tail(10), use_container_width=True)
        else:
            st.warning("No temporal traces recorded yet.")

    except Exception as e:
        st.error(f"Dashboard Update Error: {e}")
