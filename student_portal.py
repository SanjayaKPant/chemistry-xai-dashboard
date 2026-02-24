import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- HELPERS ---
def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("कृपया पहिले लगइन गर्नुहोस् (Please login first)")
        st.stop()
        
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 साथी (Saathi) AI", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 साथी (Saathi) AI":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_metacognitive_dashboard(user.get('User_ID'))

# --- 1. DASHBOARD ---
def render_dashboard(user):
    st.title(f"नमस्ते, {user['Name']}! 🙏")
    st.markdown("### साथी (Saathi) AI सिकाई पोर्टलमा स्वागत छ")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🎯 **Module 1:** पदार्थको अवस्था (States of Matter)")
        if st.button("Start Learning"):
            st.session_state.current_nav = "📚 Learning Modules"
            st.rerun()
    with col2:
        st.success("🤖 **Saathi AI:** तपाईंको व्यक्तिगत विज्ञान शिक्षक।")

# --- 2. MODULES WITH TIER 5-6 REVISION ---
def render_modules(student_group):
    st.title("📚 Learning Modules")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            m_name = row['Sub_Title']
            st.markdown(f"### 📖 {m_name}")
            
            # State Management for Revision
            is_mastery = st.session_state.get(f"mastery_{m_name}", False)

            if not is_mastery:
                # --- TIERS 1-4 ---
                st.write(f"**प्रश्न (Question):** {row['Diagnostic_Question']}")
                ans = st.radio(f"Tier 1", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                conf1 = st.select_slider(f"Tier 2 (Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                reason = st.text_area(f"Tier 3 (Reasoning)", key=f"t3_{idx}")
                conf2 = st.select_slider(f"Tier 4 (Reasoning Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

                if st.button("Submit Initial Thoughts", key=f"btn_{idx}"):
                    # Log Assessment with placeholders for 5 & 6
                    log_assessment(st.session_state.user['User_ID'], student_group, m_name, ans, conf1, reason, conf2, "INITIAL", get_nepal_time(), "", "")
                    st.session_state.current_topic = m_name
                    st.session_state.logic_tree = row['Socratic_Tree']
                    st.success("अब साथी AI सँग छलफल गर्नुहोस्!")
            else:
                # --- TIERS 5-6 (Ingenious Revision) ---
                st.warning("🌟 परिमार्जन मोड (Revision Mode Active)")
                st.write(f"**अघिल्लो तर्क (Previous Reason):** {st.session_state.get('last_tier3_reasoning', 'N/A')}")
                rev_reason = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Reasoning)", key=f"t5_{idx}")
                rev_conf = st.select_slider("Tier 6: नयाँ आत्मविश्वास (Revised Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")

                if st.button("Save Final Mastery", key=f"m_btn_{idx}"):
                    log_assessment(st.session_state.user['User_ID'], student_group, m_name, "REVISED", "N/A", "N/A", "N/A", "MASTERY", get_nepal_time(), rev_reason, rev_conf)
                    st.session_state[f"mastery_{m_name}"] = False
                    st.balloons()
                    st.rerun()
            st.divider()
    except Exception as e: st.error(f"Error: {e}")

# --- 3. SAATHI AI (MASTERY DETECTION) ---
def render_ai_chat(group_name):
    st.header("🤖 साथी (Saathi) AI")
    topic = st.session_state.get('current_topic', 'Science')
    logic = st.session_state.get('logic_tree', 'General Principles')

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"Socratic tutor for Grade 8-10. Focus on: {logic}."}]

    for m in st.session_state
