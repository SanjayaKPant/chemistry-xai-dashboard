import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

def show():
    if 'user' not in st.session_state: return
    user = st.session_state.user
    student_group = str(user.get('Group', 'School A')).strip()
    
    st.sidebar.title(f"🎓 {user.get('Name')}")
    st.sidebar.info(f"Cohort: {student_group}")
    
    if 'current_nav' not in st.session_state:
        st.session_state.current_nav = "🏠 Dashboard"
        
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic Tutor", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.current_nav))
    st.session_state.current_nav = choice

    if choice == "🏠 Dashboard":
        render_dashboard(user, student_group)
    elif choice == "📚 Learning Modules":
        render_modules(student_group)
    elif choice == "🤖 Socratic Tutor":
        render_ai_chat(student_group)
    elif choice == "📈 My Progress":
        render_progress(user.get('User_ID'))

def render_modules(student_group):
    # MAIN TITLES (Decreasing Font Size)
    st.markdown("<h1 style='text-align: center; color: #0E1117;'>Advanced Chemistry Instructional Portal</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #4B5563;'>Learning & Assessment Path</h2>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.get('last_submission_success'):
        st.success("✅ Assessment Recorded!")
        st.markdown("### Next Step: Socratic Discussion")
        if st.button("🚀 Proceed to AI Tutor", use_container_width=True):
            st.session_state.current_nav = "🤖 Socratic Tutor"
            st.session_state.last_submission_success = False
            st.rerun()
        return 

    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            q_num = idx + 1
            
            # MODULE HEADER
            st.markdown(f"""
                <div style="background-color:#E1E8F0; padding:10px; border-radius:5px; margin-bottom:10px;">
                    <h2 style="color:#1E3A8A; margin:0; font-size:24px;">📖 Module {q_num}: {row['Sub_Title']}</h2>
                </div>
            """, unsafe_allow_html=True)

            # SIDE-BY-SIDE RESOURCES
            c1, c2 = st.columns(2)
            with c1: st.link_button("📄 PDF Notes", row['File_Links (PDF/Images)'], use_container_width=True)
            with c2: st.link_button("📺 Video", row['Video_Links'], use_container_width=True)

            # COMPACT QUESTION BLOCK
            st.markdown(f"""
                <div style="background-color:#F8FAFC; padding:10px; border-radius:8px; border-left: 4px solid #3B82F6; margin-top:10px;">
                    <p style="font-size:17px; font-weight:500; color:#1E293B;">{row['Diagnostic_Question']}</p>
                </div>
            """, unsafe_allow_html=True)

            # --- 4 TIERS (VERTICAL ORDER) ---
            st.write("")
            ans = st.radio("**Tier 1: Choose the correct option**", 
                           [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"q{idx}_t1")
            
            conf1 = st.select_slider("**Tier 2: Answer Confidence**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t2")
            
            reason = st.text_area("**Tier 3: Scientific Reasoning**", 
                                  placeholder="Provide a chemical explanation for your choice...", key=f"q{idx}_t3")
            
            conf2 = st.select_slider("**Tier 4: Reasoning Confidence**", 
                                     options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"q{idx}_t4")

            if st.button(f"Submit Assessment {q_num}", use_container_width=True):
                # VALIDATION: Reason cannot be empty
                if not reason.strip() or len(reason.strip()) < 10:
                    st.error("⚠️ Please provide a detailed scientific reason (Tier 3) before submitting.")
                else:
                    success = log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], ans, conf1, reason, conf2, "Complete", "")
                    if success:
                        st.session_state.current_topic = row['Sub_Title']
                        st.session_state.logic_tree = row['Socratic_Tree']
                        st.session_state.last_submission_success = True
                        log_temporal_trace(st.session_state.user['User_ID'], "QUIZ_COMPLETE", row['Sub_Title'])
                        st.rerun()
            st.divider()

    except Exception as e:
        st.error(f"Module Error: {e}")

def render_ai_chat(group):
    if group not in ["School A", "Exp_A"]:
        st.warning("Access Restricted to Experimental Groups.")
        return
    if 'current_topic' not in st.session_state:
        st.info("Please submit a module diagnostic first.")
        return

    st.markdown(f"<h1 style='color: #1E3A8A;'>🤖 Socratic Tutor</h1>", unsafe_allow_html=True)
    st.caption(f"Topic: {st.session_state.current_topic}")

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except:
        st.error("AI HANDSHAKE FAILED.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Discuss your reasoning..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        sys_p = (f"You are a Socratic Tutor. Topic: {st.session_state.current_topic}. "
                 f"Socratic Logic: {st.session_state.logic_tree}. "
                 "Strict Rule: Never give answers. Ask one guiding question to scaffold the student.")
        
        try:
            # FIXED: Removed RequestOptions(api_version='v1') which caused the error
            resp = model.generate_content(f"{sys_p}\nStudent: {prompt}")
            with st.chat_message("assistant"):
                st.markdown(resp.text)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
            log_temporal_trace(st.session_state.user['User_ID'], "AI_TURN", st.session_state.current_topic)
        except Exception as e:
            st.error(f"AI sync error: {e}")

# (Rest of the functions: render_dashboard and render_progress remain similar)
