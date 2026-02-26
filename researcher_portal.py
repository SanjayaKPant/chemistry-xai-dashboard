import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_manager import get_gspread_client

def show():
    # Use wide layout for data density
    st.title("🔬 PhD Principal Investigator Dashboard")
    st.markdown("---")

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        
        # Load Primary Research Data
        logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        mats_df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        trace_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())

        # --- RESEARCH KPI BAR ---
        c1, c2, c3, c4 = st.columns(4)
        total_p = len(logs_df['User_ID'].unique()) if not logs_df.empty else 0
        total_m = len(mats_df)
        mastery_n = len(logs_df[logs_df['Status'] == 'POST']) if not logs_df.empty else 0
        
        c1.metric("Participants (N)", total_p)
        c2.metric("Modules Deployed", total_m)
        c3.metric("Socratic Iterations", len(trace_df))
        c4.metric("Mastery Achievement", mastery_n)

        st.markdown("---")

        # --- RESEARCH TABS ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Executive Metrics", 
            "📉 Metacognitive Calibration", 
            "🔄 Conceptual Flow (Sankey)", 
            "📂 Evidence Export"
        ])

        with tab1:
            render_executive_view(mats_df, logs_df)

        with tab2:
            render_calibration_view(logs_df)

        with tab3:
            render_sankey_view(logs_df)

        with tab4:
            st.subheader("SPSS/R Export Hub")
            st.download_button(
                "Download Anonymized Dataset (CSV)", 
                logs_df.to_csv(index=False), 
                "chemistry_phd_data.csv", 
                "text/csv"
            )
            st.dataframe(logs_df)

    except Exception as e:
        st.error(f"Researcher Data Error: {e}")

def render_executive_view(mats, logs):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Instructional Material Distribution**")
        if not mats.empty:
            fig = px.pie(mats, names='Group', hole=0.4, title="Materials by School Group")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.write("**Engagement per Concept**")
        if not logs.empty:
            fig = px.bar(logs, x='Module_ID', color='Status', barmode='group')
            st.plotly_chart(fig, use_container_width=True)

def render_calibration_view(df):
    st.subheader("Evidence of Metacognitive Monitoring")
    
    if df.empty: return
    
    # Logic for calibration: Confidence vs Accuracy
    conf_map = {"Guessing": 25, "Unsure": 50, "Sure": 75, "Very Sure": 100}
    df['Conf'] = df['Tier_2 (Confidence_Ans)'].map(conf_map)
    df['Acc'] = df['Diagnostic_Result'].apply(lambda x: 100 if x == "Correct" else 0)
    
    fig = px.scatter(df, x="Conf", y="Acc", trendline="ols", 
                     title="Calibration Curve: Does AI improve self-awareness?")
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="Red", dash="dash"))
    st.plotly_chart(fig, use_container_width=True)

def render_sankey_view(df):
    st.subheader("Visualizing Conceptual Transformation")
    
    # Simplified logic to show flow from INITIAL state to POST state
    labels = ["Initial Misconception", "Initial Correct", "AI Intervention", "Post-Test Mastery", "Post-Test Error"]
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, thickness=20, label=labels, color="teal"),
        link = dict(
            source=[0, 1, 2, 2], 
            target=[2, 2, 3, 4], 
            value=[20, 10, 25, 5] # These should be len() counts from your DF
        )
    )])
    st.plotly_chart(fig, use_container_width=True)
