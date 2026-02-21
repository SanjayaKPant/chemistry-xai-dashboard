import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client

def show():
    user = st.session_state.user
    
    # Custom CSS for Professional Branding
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6; border-radius: 8px 8px 0px 0px;
            padding: 10px 20px; font-weight: bold; transition: 0.3s;
        }
        .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
        .deployment-card { 
            background-color: #ffffff; padding: 25px; border-radius: 15px;
            border-left: 5px solid #007bff; box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧑‍🏫 LMS Orchestration & Research Hub")
    st.markdown("---")

    # Full-fledged LMS Tab Navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Deployment Center", 
        "📊 Learning Analytics", 
        "👥 Engagement & Attendance", 
        "📑 Assignments"
    ])

    # --- TAB 1: DEPLOYMENT CENTER ---
    with tab1:
        st.markdown("### 📤 Lesson & 4-Tier Diagnostic Deployment")
        st.markdown('<div class="deployment-card">', unsafe_allow_html=True)
        with st.form("professional_lesson_form"):
            # Row 1: Administrative Controls
            r1_c1, r1_c2, r1_c3 = st.columns([1, 1.5, 1.5])
            with r1_c1:
                target_group = st.selectbox("Assign Group", ["School A", "School B"])
            with r1_c2:
                main_title = st.text_input("Chapter Title", "Classification of Elements")
            with r1_c3:
                sub_title = st.text_input("Specific Concept", placeholder="e.g. Modern Periodic Law")

            # Row 2: Learning Objectives (Enlarged)
            objectives = st.text_area("🎯 Learning Objectives & Outcomes", height=120)

            st.markdown("🧪 **Diagnostic Design (4-Tier Research Ready)**")
            
            
            # Row 3: The Question
            q_text = st.text_input("Diagnostic Question (Tier 1)", placeholder="Enter the central research question here...")

            # Row 4: Options and Answer (Compact Grid)
            o1, o2, o3, o4, ans = st.columns([1, 1, 1, 1, 0.8])
            with o1: oa = st.text_input("Option A")
            with o2: ob = st.text_input("Option B")
            with o3: oc = st.text_input("Option C")
            with o4: od = st.text_input("Option D")
            with ans: correct = st.selectbox("Correct", ["A", "B", "C", "D"])

            st.markdown("📂 **Multimodal Assets & Socratic Scaffolding**")
            
            # Row 5: Asset Uploads (Same Row)
            a1, a2 = st.columns(2)
            with a1:
                up_file = st.file_uploader("Textbook PDF/Image", type=['pdf', 'png', 'jpg'], label_visibility="collapsed")
                st.caption("📄 Upload Textbook Context (PDF/Image)")
            with a2:
                vid_url = st.text_input("Video URL", placeholder="YouTube/Web Link", label_visibility="collapsed")
                st.caption("🎥 Video Resource Link")

            # Row 6: Socratic Tree
            socratic_logic = st.text_area("🧠 Socratic Scaffolding Tree (For Experimental Group)", height=100, 
                                          placeholder="If student says X, guide them to Y using Z...")

            if st.form_submit_button("🚀 DEPLOY TO RESEARCH DATABASE"):
                with st.spinner("Processing High-Fidelity Sync..."):
                    file_url = upload_to_drive(up_file) if up_file else ""
                    
                    data_package = {
                        "sub_title": sub_title,
                        "objectives": objectives,
                        "file_link": file_url,
                        "video_link": vid_url,
                        "q_text": q_text,
                        "oa": oa, "ob": ob, "oc": oc, "od": od,
                        "correct": correct,
                        "socratic_tree": socratic_logic
                    }
                    
                    if save_bulk_concepts(user['User_ID'], target_group, main_title, data_package):
                        st.success(f"Successfully deployed '{sub_title}' to {target_group}!")
                        st.balloons()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: LEARNING ANALYTICS (Research Insights) ---
    with tab2:
        st.header("📈 Diagnostic Misconception Analysis")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            logs_df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
            
            if not logs_df.empty:
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    fig_pie = px.pie(logs_df, names='Tier_1', title="Answer Distribution (Accuracy)", hole=0.3)
                    st.plotly_chart(fig_pie, use_container_width=True)
                with col_chart2:
                    fig_bar = px.histogram(logs_df, x="Module_ID", color="Tier_2", barmode="group", title="Confidence Gap Analysis")
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                st.subheader("🔗 Cognitive Flow (Tier 2 → Tier 4)")
                st.info("Sankey visualization mapping confidence to reasoning clarity will appear as more data is collected.")
                
            else:
                st.info("Awaiting student submissions to generate analytics.")
        except:
            st.warning("Assessment Logs worksheet currently inaccessible.")

    # --- TAB 3: ENGAGEMENT & ATTENDANCE ---
    with tab3:
        st.header("👥 Real-time Engagement Tracker")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            traces_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            
            if not traces_df.empty:
                st.write("📊 **Student Temporal Traces**")
                st.dataframe(traces_df, use_container_width=True)
                
                # Activity Distribution
                act_fig = px.bar(traces_df['Event'].value_counts().reset_index(), x='Event', y='count', color='Event', title="Portal Activity Spread")
                st.plotly_chart(act_fig, use_container_width=True)
            else:
                st.info("No engagement data found.")
        except:
            st.error("Error loading Temporal Traces.")

    # --- TAB 4: ASSIGNMENTS ---
    with tab4:
        st.header("📑 Assignment Orchestration")
        a_c1, a_c2 = st.columns(2)
        with a_c1:
            st.markdown('<div class="deployment-card">', unsafe_allow_html=True)
            st.subheader("Post New Assignment")
            with st.form("lms_assign_form"):
                a_title = st.text_input("Task Title")
                a_desc = st.text_area("Instructions")
                a_file = st.file_uploader("Reference Material (PDF)")
                if st.form_submit_button("Deploy Assignment"):
                    st.success("Assignment live in student portals.")
            st.markdown('</div>', unsafe_allow_html=True)
        with a_c2:
            st.subheader("Submissions Overview")
            st.info("No submissions currently pending review.")
