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
        trace_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())

        if logs_df.empty:
            st.warning("⚠️ No data found in Assessment_Logs. Charts will populate once students finish modules.")
            return

        # --- DATA CLEANING FOR RESEARCH ---
        # Ensure role is stripped of whitespace
        logs_df['Status'] = logs_df['Status'].astype(str).str.strip().upper()

        # --- KPI METRICS ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Participants (N)", len(logs_df['User_ID'].unique()))
        c2.metric("Initial Diagnostics", len(logs_df[logs_df['Status'] == 'INITIAL']))
        c3.metric("Post-AI Mastery Logs", len(logs_df[logs_df['Status'] == 'POST']))

        tab1, tab2, tab3 = st.tabs(["📉 Calibration & Validity", "🔄 Conceptual Flow", "📂 Data Export"])

        # --- TAB 1: CALIBRATION ---
        with tab1:
            render_calibration_logic(logs_df)

        # --- TAB 2: CONCEPTUAL FLOW (SANKEY) ---
        with tab2:
            st.subheader("Socratic Transformation Map")
            st.write("Visualizing the transition from Initial Misconception to Scientific Mastery.")
            render_dynamic_sankey(logs_df)

        # --- TAB 3: DATA EXPORT ---
        with tab3:
            st.subheader("Raw Evidence Hub")
            st.write("Download the 12-column dataset for SPSS/R-studio analysis.")
            csv_data = logs_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Research CSV", csv_data, "chemistry_phd_data.csv", "text/csv")
            st.dataframe(logs_df)

    except Exception as e:
        st.error(f"Researcher Portal Sync Error: {e}")

# --- ADVANCED VIZ FUNCTIONS ---

def render_calibration_logic(df):
    conf_map = {"Guessing": 25, "Unsure": 50, "Sure": 75, "Very Sure": 100}
    df['Conf_Num'] = df['Tier_2 (Confidence_Ans)'].map(conf_map)
    # Binary accuracy for calibration
    df['Acc_Num'] = df['Diagnostic_Result'].apply(lambda x: 100 if str(x).strip() == "Correct" else 0)
    
    fig = px.scatter(df, x="Conf_Num", y="Acc_Num", trendline="ols",
                     labels={"Conf_Num": "Confidence (%)", "Acc_Num": "Actual Accuracy (%)"},
                     title="Metacognitive Calibration Curve")
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="Red", dash="dash"))
    st.plotly_chart(fig, width='stretch')
    

def render_dynamic_sankey(df):
    # DYNAMIC DATA COUNTING
    # We count how many entries are Initial vs Post
    n_initial_wrong = len(df[(df['Status'] == 'INITIAL') & (df['Diagnostic_Result'] != 'Correct')])
    n_initial_right = len(df[(df['Status'] == 'INITIAL') & (df['Diagnostic_Result'] == 'Correct')])
    n_post_mastery = len(df[(df['Status'] == 'POST') & (df['Diagnostic_Result'] == 'Correct')])
    n_post_error = len(df[(df['Status'] == 'POST') & (df['Diagnostic_Result'] != 'Correct')])

    labels = ["Initial: Incorrect", "Initial: Correct", "Saathi AI Chat", "Post: Mastery", "Post: Persistent Error"]
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, thickness=20, label=labels, color="teal"),
        link = dict(
            source=[0, 1, 2, 2], # Flow origins
            target=[2, 2, 3, 4], # Flow destinations
            value=[n_initial_wrong, n_initial_right, n_post_mastery, n_post_error]
        )
    )])
    st.plotly_chart(fig, width='stretch')
