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
st.markdown(f"**Analyzing:** {topic} | **Threshold:** {confidence_threshold}%")

# 3. Data Loading Logic
try:
    df = pd.read_csv("mock_data.csv")
    
    # Filter by Topic
    filtered_df = df[df["Topic"] == topic]
    
    # Logic for "Confident but Wrong" (CBW)
    # CBW = High Confidence (>= threshold) but Low Score (< 50)
    cbw_students = filtered_df[(filtered_df["Confidence_Level"] >= confidence_threshold) & (filtered_df["Score"] < 50)]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Student Overview")
        st.dataframe(filtered_df, use_container_width=True)

    with col2:
        st.subheader("🚨 Critical Misconceptions")
        if not cbw_students.empty:
            st.error(f"Found {len(cbw_students)} student(s) at risk!")
            st.table(cbw_students[["Student_ID", "Score", "Confidence_Level"]])
        else:
            st.success("No 'Confident but Wrong' cases found at this threshold.")

except FileNotFoundError:
    st.info("Please ensure 'mock_data.csv' is uploaded to your GitHub repository.")
