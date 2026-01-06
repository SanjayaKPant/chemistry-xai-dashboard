import streamlit as st

# --- SIDEBAR: THE TEACHER'S TOOLS ---
st.sidebar.header("Dashboard Filters")

# 1. Selectbox for Chemistry Topics (From your Knowledge Graph)
topic = st.sidebar.selectbox(
    "Select Chemistry Topic:",
    ["Periodic Table", "Chemical Reaction", "Acids & Bases", "Atomic Structure", "Chemical Bonding"]
)

# 2. Slider for Confidence (Linking to your Tier 3 Diagnostic)
# We want to filter students who are 'Confident' but 'Wrong'
confidence_threshold = st.sidebar.slider(
    "Set Misconception Confidence Threshold (%):",
    min_value=0, max_value=100, value=75
)

# --- MAIN AREA: THE INSIGHTS ---
st.title("PhD Research: XAI Misconception Dashboard")

st.header(f"Analyzing Topic: {topic}")

st.write(f"Currently showing students who hold misconceptions with a confidence level above **{confidence_threshold}%**.")

# A placeholder for our future heatmap
st.info("The Misconception Heatmap will appear below this section on Day 7.")


import pandas as pd

# Load the data we just created
df = pd.read_csv("mock_data.csv")

# Filter data based on the sidebar selection you built
filtered_df = df[df["Topic"] == topic]

st.subheader(f"Data Preview for {topic}")
st.write(filtered_df)

# Logic to highlight "Confident but Wrong" students
high_confidence_issues = filtered_df[(filtered_df["Confidence_Level"] >= confidence_threshold) & (filtered_df["Score"] < 50)]

if not high_confidence_issues.empty:
    st.warning(f"⚠️ Found {len(high_confidence_issues)} student(s) with high confidence but low scores in {topic}.")
    st.dataframe(high_confidence_issues)
else:
    st.success("No critical misconceptions detected at this threshold.")
