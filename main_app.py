import streamlit as st
import pandas as pd

st.set_page_config(page_title="XAI Chem-DKT Dashboard", layout="wide")

# 1. Sidebar Configuration
st.sidebar.header("Research Parameters")
topic = st.sidebar.selectbox(
    "Select Chemistry Topic:",
    ["Periodic Table", "Chemical Reaction", "Acids & Bases", "Atomic Structure", "Chemical Bonding"]
)
confidence_threshold = st.sidebar.slider("Confidence Threshold (%)", 0, 100, 75)

# 2. Main Title
st.title("🧪 XAI Misconception Diagnostic")

# 3. Create Tabs
tab1, tab2 = st.tabs(["🏠 Research Overview", "📊 Diagnostic Tool"])

with tab1:
    st.header("Project Welcome")
    st.write("This dashboard analyzes Chemistry DKT data from schools in Nepal.")
    st.info("The Misconception Heatmap will appear in this section on Day 7.")

with tab2:
    # 4. Data Loading Logic (NOW PROPERLY INDENTED)
    try:
        df = pd.read_csv("mock_data.csv")
        filtered_df = df[df["Topic"] == topic]
        cbw_students = filtered_df[(filtered_df["Confidence_Level"] >= confidence_threshold) & (filtered_df["Score"] < 50)]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Student Overview")
            st.dataframe(filtered_df, use_container_width=True)
        with col2:
           import plotly.express as px

st.divider()
st.subheader("🔥 Misconception Heatmap: Confidence vs. Score")

# Create a scatter plot that acts as a heatmap
fig = px.scatter(
    filtered_df, 
    x="Score", 
    y="Confidence_Level",
    color="Score",
    text="Student_ID",
    size_max=60,
    labels={"Confidence_Level": "Confidence (%)", "Score": "Knowledge Score"},
    color_continuous_scale="RdYlGn" # Red-Yellow-Green scale
)

# Add a "Danger Zone" line for misconceptions
fig.add_hline(y=confidence_threshold, line_dash="dash", line_color="red", annotation_text="High Confidence")
fig.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="Low Knowledge")

st.plotly_chart(fig, use_container_width=True)
