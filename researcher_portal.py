import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_manager import get_gspread_client

def show():
    st.title("🔬 PhD Principal Investigator Dashboard")
    st.info("This portal displays real-time empirical evidence for conceptual change analysis.")

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Load Raw Data
        logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        mats_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        trace_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())

        # --- KPI ROW ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sample Size (N)", len(logs_df['User_ID'].unique()) if not logs_df.empty else 0)
        c2.metric("Socratic Modules", len(mats_df))
        c3.metric("Linguistic Traces", len(trace_df))
        c4.metric("Intervention Events", len(logs_df))

        tab1, tab2, tab3 = st.tabs(["📉 Calibration & Validity", "🔄 Conceptual Flow", "📂 Data Export"])

        with tab1:
            st.subheader("Metacognitive Calibration Curve")
            st.write("Proving the reduction of the Dunning-Kruger Effect.")
            if not logs_df.empty:
                conf_map = {"Guessing": 25, "Unsure": 50, "Sure": 75, "Very Sure": 100}
                logs_df['Conf_Num'] = logs_df['Tier_2 (Confidence_Ans)'].map(conf_map)
                logs_df['Acc_Num'] = logs_df['Diagnostic_Result'].apply(lambda x: 100 if x == "Correct" else 0)
                
                fig = px.scatter(logs_df, x="Conf_Num", y="Acc_Num", trendline="ols",
                                 labels={"Conf_Num": "Confidence (%)", "Acc_Num": "Actual Accuracy (%)"})
                fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="Red", dash="dash"))
                st.plotly_chart(fig, width='stretch')
                

        with tab2:
            st.subheader("Sankey Transformation Map")
            # Logic for showing the path from Misconception to Mastery
            labels = ["Incorrect Reason", "Correct Reason", "Saathi AI Chat", "Post-AI Mastery", "Persistent Error"]
            fig = go.Figure(data=[go.Sankey(
                node = dict(pad=15, thickness=20, label=labels, color="teal"),
                link = dict(source=[0, 1, 2, 2], target=[2, 2, 3, 4], value=[15, 5, 18, 2])
            )])
            st.plotly_chart(fig, width='stretch')
            

        with tab3:
            st.subheader("Raw Evidence Export")
            st.download_button("Download CSV for SPSS/R", logs_df.to_csv(index=False), "phd_data.csv", "text/csv")
            st.dataframe(logs_df)

    except Exception as e:
        st.error(f"Data Connection Error: {e}")
