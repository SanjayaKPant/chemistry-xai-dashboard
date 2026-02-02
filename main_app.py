import streamlit as st
import pandas as pd
from datetime import datetime
from database_manager import conn, save_quiz_responses, log_temporal_trace, save_temporal_traces
from research_engine import get_agentic_hint

# --- 1. CONFIGURATION & SESSION STATE ---
st.set_page_config(page_title="AI-Chem Research Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'trace_buffer' not in st.session_state:
    st.session_state.trace_buffer = []

# --- 2. AUTHENTICATION LOGIC ---
def check_login(user_id):
    try:
        # Fetching the full participant list
        df = conn.read(
            spreadsheet=st.secrets["gsheets"]["spreadsheet"],
            worksheet="Participants",
            ttl=0
        )
        # Force the column to string to ensure matching works
        df['User_ID'] = df['User_ID'].astype(str)
        user_row = df[df['User_ID'] == str(user_id)]
        
        if not user_row.empty:
            st.session_state.user_data = user_row.iloc[0].to_dict()
            st.session_state.logged_in = True
            log_temporal_trace("LOGIN_SUCCESS", details=user_id)
            return True
        else:
            st.error("User ID not found.")
            return False
    except Exception as e:
        st.error(f"Login Connection Error: {e}")
        return False
    # --- TIER 1: CONTENT ---
    t1 = st.radio("Tier 1: Where are electrons primarily located?", 
                  ["Select...", "Inside the Nucleus", "In the Electron Cloud"], key="q1_v3")

    # --- AGENTIC SCALFFOLDING (The Blue Box) ---
    if t1 != "Select...":
        # Testing bypass for S001 or Experimental Group A
        if user['Group'] == "Exp_A" or user['User_ID'] == "S001":
            hint = get_agentic_hint("atom_structure_01", t1)
            if hint:
                st.info(f"🤖 **AI Tutor:** {hint}")
                log_temporal_trace("HINT_VIEWED", details=t1)

    st.divider()

    # --- TIERS 2, 3, 4: CONFIDENCE & REASONING ---
    t2 = st.select_slider("Tier 2: How confident are you in this choice?", 
                          options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q2_v3")
    
    t3 = st.text_area("Tier 3: Scientific Reasoning (Explain your choice below):", key="q3_v3")
    
    t4 = st.select_slider("Tier 4: How confident are you in your explanation?", 
                          options=["Not Confident", "Somewhat", "Confident", "Very Confident"], key="q4_v3")

    # --- SINGLE SUBMIT BUTTON ---
    if st.button("Submit Research Data", key="final_btn"):
        if t1 == "Select...":
            st.warning("Please answer Tier 1.")
        else:
            quiz_data = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "User_ID": user['User_ID'],
                "Tier_1": t1, "Tier_2": t2, "Tier_3": t3, "Tier_4": t4
            }
            if save_quiz_responses(conn, quiz_data):
                save_temporal_traces(conn, st.session_state.trace_buffer)
                st.success("✅ Assessment & Temporal Traces Synced to Google Drive!")
                st.balloons()

# --- 4. NAVIGATION & ROUTING ---
if not st.session_state.logged_in:
    st.title("🔐 Researcher Login")
    u_id = st.text_input("Enter User ID (e.g., S001):").upper()
    if st.button("Login"):
        if check_login(u_id):
            st.rerun()
else:
    with st.sidebar:
        st.write(f"👤 **User:** {st.session_state.user_data['Name']}")
        st.write(f"📊 **Group:** {st.session_state.user_data['Group']}")
        page = st.selectbox("Go to:", ["Quiz", "Research Dashboard"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if page == "Quiz":
        show_quiz()
    else:
        from admin_dashboard import show_admin_portal
        show_admin_portal()

# --- 5. FINALLY SUBMIT BUTTON ---
if st.button("Submit Research Data", key="final_submit"):
    if not tier1_choice:
        st.warning("Please answer Tier 1.")
    else:
        quiz_data = {
            "User_ID": st.session_state.user_data['User_ID'],
            "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Tier_1": tier1_choice,
            "Tier_2": tier2_conf,
            "Tier_3": tier3_reason,
            "Tier_4": tier4_conf
        }
        
        # Save to Google Sheets
        if save_quiz_responses(quiz_data):
            save_temporal_traces(st.session_state.trace_buffer)
            st.success("Research & Temporal Traces Synced to Google Drive!")
            st.balloons()
