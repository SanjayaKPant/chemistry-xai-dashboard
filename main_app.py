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
