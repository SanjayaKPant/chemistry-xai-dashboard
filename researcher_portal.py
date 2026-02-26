import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_manager import get_gspread_client

def show():
    st.title("🔬 PhD Principal Investigator Dashboard")
    st.info("Empirical Evidence Hub for Socratic Learning Analysis")

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Load Raw Data
        logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        
        if logs_df.empty:
            st.warning("⚠️ No data found in Assessment_Logs.")
            return

        # --- THE FIX: ROBUST DATA CLEANING ---
        # 1. Convert everything to string first to avoid 'Series' errors
        # 2. Use .str accessor to apply string methods to the whole column safely
        logs_df['Status'] = logs_df['Status'].astype(str).str.strip().str.upper()
        logs_df['Diagnostic_Result'] = logs_df['Diagnostic_Result'].astype(str).str.strip()

        # --- KPI METRICS ---
        c1, c2, c3 = st.columns(3)
        # Filter safely using the cleaned strings
        initial_count = len(logs_df[logs_df['Status'] == 'INITIAL'])
        post_count = len(logs_df[logs_df['Status'] == 'POST'])
        
        c1.metric("Total Participants (N)", len(logs_df['User_ID'].unique()))
        c2.metric("Initial Diagnostics", initial_count)
        c3.metric("Post-AI Mastery Logs", post_count)

        tab1, tab2, tab3 = st.tabs(["📉 Calibration & Validity", "🔄 Conceptual Flow", "📂 Data Export"])

        with tab1:
            render_calibration_logic(logs_df)

        with tab2:
            st.subheader("Socratic Transformation Map")
            render_dynamic_sankey(logs_df)

        with tab3:
            st.subheader("Raw Evidence Hub")
            csv_data = logs_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Research CSV", csv_data, "phd_data.csv", "text/csv")
            st.dataframe(logs_df)

    except Exception as e:
        st.error(f"Researcher Portal Sync Error: {e}")

def render_calibration_logic(df):
    # Ensure numeric conversion for plotting
    conf_map = {"Guessing": 25, "Unsure": 50, "Sure": 75, "Very Sure": 100}
    df['Conf_Num'] = df['Tier_2 (Confidence_Ans)'].map(conf_map).fillna(0)
    df['Acc_Num'] = df['Diagnostic_Result'].apply(lambda x: 100 if x == "Correct" else 0)
    
    fig = px.scatter(df, x="Conf_Num", y="Acc_Num", trendline="ols",
                     labels={"Conf_Num": "Confidence (%)", "Acc_Num": "Actual Accuracy (%)"},
                     title="Metacognitive Calibration Curve")
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="Red", dash="dash"))
    st.plotly_chart(fig, width='stretch')
    

def render_dynamic_sankey(df):
    # Dynamic counting based on the cleaned 'Status' and 'Diagnostic_Result'
    n_initial_wrong = len(df[(df['Status'] == 'INITIAL') & (df['Diagnostic_Result'] != 'Correct')])
    n_initial_right = len(df[(df['Status'] == 'INITIAL') & (df['Diagnostic_Result'] == 'Correct')])
    n_post_mastery = len(df[(df['Status'] == 'POST') & (df['Diagnostic_Result'] == 'Correct')])
    n_post_error = len(df[(df['Status'] == 'POST') & (df['Diagnostic_Result'] != 'Correct')])

    labels = ["Initial: Incorrect", "Initial: Correct", "Saathi AI Chat", "Post: Mastery", "Post: Persistent Error"]
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, thickness=20, label=labels, color="teal"),
        link = dict(
            source=[0, 1, 2, 2], 
            target=[2, 2, 3, 4], 
            value=[max(n_initial_wrong, 0.1), max(n_initial_right, 0.1), max(n_post_mastery, 0.1), max(n_post_error, 0.1)]
        )
    )])
    st.plotly_chart(fig, width='stretch')
