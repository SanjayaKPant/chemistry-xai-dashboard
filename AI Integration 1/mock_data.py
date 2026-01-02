import streamlit as st
import pandas as pd # This is for handling data tables

# --- 1. MOCK DATA (Simulating your AI Outputs) ---
# In Phase 2, this will come from your GAT-DKT model
data = {
    'Student Name': ['Anil', 'Sita', 'Ram', 'Gita', 'Binod'],
    'Misconception': ['pH Scale', 'Ion Concentration', 'pH Scale', 'Neutralization', 'Ion Concentration'],
    'Confidence Level (%)': [85, 40, 92, 30, 78]
}
df = pd.DataFrame(data)

# --- 2. SIDEBAR ---
st.sidebar.header("Teacher Controls")

# Selection for the topic
topic_filter = st.sidebar.selectbox("Filter by Topic:", ["All", "pH Scale", "Ion Concentration", "Neutralization"])

# Slider for Confidence
confidence_threshold = st.sidebar.slider("Minimum Confidence to Flag:", 0, 100, 75)

# --- 3. MAIN DASHBOARD ---
st.title("XAI Misconception Dashboard")
st.subheader(f"Current View: {topic_filter}")

# --- 4. THE RESEARCH LOGIC (Filtering) ---
# We filter the data based on the slider and the dropdown
filtered_df = df[df['Confidence Level (%)'] >= confidence_threshold]

if topic_filter != "All":
    filtered_df = filtered_df[filtered_df['Misconception'] == topic_filter]

# --- 5. DISPLAYING RESULTS ---
st.write(f"Showing students with over **{confidence_threshold}%** confidence in their error:")

if filtered_df.empty:
    st.warning("No students match these criteria. Your class seems to understand this well!")
else:
    # This draws the table
    st.table(filtered_df)

# XAI Explanation for the PhD Thesis
with st.expander("Why are these students flagged?"):
    st.write("""
        These students are flagged because they have a **High-Confidence Misconception**. 
        According to your 3-Tier Diagnostic research, these students are 'Confident but Wrong,' 
        meaning they require immediate intervention as they are unlikely to correct themselves.
    """)


