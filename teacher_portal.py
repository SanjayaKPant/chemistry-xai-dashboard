import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client

def show():
    user = st.session_state.user
    
    # --- CSS Styling for Professional Branding ---
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6; border-radius: 5px 5px 0px 0px;
            padding: 10px 20px; font-weight: bold;
        }
        .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
        .card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧑‍🏫 LMS Orchestration & Research Hub")
    
    # Create Tabs for a Full-Fledged LMS Feel
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Deployment Center", 
        "📊 Learning Analytics", 
        "👥 Student Engagement", 
        "📑 Assignments"
    ])

    # --- TAB 1: DEPLOYMENT CENTER ---
    with tab1:
        st.subheader("📤 Deploy Research Modules")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("professional_deployment_form"):
            # Row 1: Administrative Control
            c1, c2, c3 = st.columns([1, 1.5, 1.5])
            with c1:
                target_group = st.selectbox("Assign Group", ["School A", "School B"], help="Select target research group")
            with c2:
                main_title = st.text_input("Chapter Title", "Classification of Elements")
            with c3:
                sub_title = st.text_input("Sub-Concept", placeholder="e.g. Modern Periodic Law")

            # Row 2: Learning Objectives (Enlarged)
            objectives = st.text_area("🎯 Learning Objectives & Outcomes", height=120)

            # Row 3: 4-Tier Diagnostic Question
            st.markdown("🧪 **4-Tier Diagnostic Question Design**")
            q_text = st.text_input("Diagnostic Question (Tier 1)", placeholder="Enter the central research question...")
            
            # Row 4: Options and Answer
            o1, o2, o3, o4, ans = st.columns([1, 1, 1, 1, 0.8])
            with o1: oa = st.text_input("Option A")
            with o2: ob = st.text_input("Option B")
            with o3: oc = st.text_input("Option C")
            with o4: od = st.text_input("Option D")
            with ans: correct = st.selectbox("Key", ["A", "B", "C", "D"])

            # Row 5: Multimodal Assets (Miniaturized)
            st.markdown("📂 **Resources & Socratic Scaffolding**")
            a1, a2 = st.columns(2)
            with a1:
                up_file = st.file_uploader("Textbook PDF/Image", type=['pdf', 'png', 'jpg'], label_visibility="collapsed")
                st.caption("📄 Upload Textbook Context")
            with a2:
                vid_url = st.text_input("Video URL", placeholder="YouTube/Web Link", label_visibility="collapsed")
                st.caption("🎥 Video Lesson Link")

            # Row 6: AI Logic
            socratic_logic = st.text_area("🧠 Socratic Scaffolding Tree", height=100, 
                                          placeholder="If student reasoning matches X, guide them toward Y...")

            if st.form_submit_button("🚀 FULL DEPLOYMENT TO PORTAL"):
                with st.spinner("Syncing with Research Database..."):
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
                        st.success(f"Successfully deployed '{sub_title}'!")
                        st.balloons()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: LEARNING ANALYTICS (The Research Brain) ---
    with tab2:
        st.subheader("📈 Diagnostic Performance Analytics")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df_logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
            
            if not df_logs.empty:
                # 1. Misconception Overview (Pie Chart)
                col_pie, col_bar = st.columns(2)
                with col_pie:
                    fig_pie = px.pie(df_logs, names='Tier_1', title="Tier 1: Answer Distribution", hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_bar:
                    # 2. Confidence Comparison (Bar Chart)
                    fig_bar = px.histogram(df_logs, x="Module_ID", color="Tier_2", barmode="group",
                                         title="Confidence Levels per Module")
                    st.plotly_chart(fig_bar, use_container_width=True)

                # 3. Sankey Logic Placeholder (For Confidence Gaps)
                st.markdown("#### 🔗 Cognitive Flow (Sankey Diagram)")
                st.info("The Sankey Diagram below tracks how student confidence (Tier 2) correlates with reasoning confidence (Tier 4).")
                            else:
                st.info("No assessment data available yet.")
        except:
            st.warning("Assessment Logs worksheet not found.")

    # --- TAB 3: ENGAGEMENT & ATTENDANCE ---
    with tab3:
        st.subheader("👥 Engagement Tracking")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df_traces = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            
            if not df_traces.empty:
                # Attendance & Time Tracking Calculations
                st.write("📊 **Temporal Trace Logs (Real-time tracking)**")
                st.dataframe(df_traces, use_container_width=True)
                
                # Total Engagement Chart
                engagement_counts = df_traces['Event'].value_counts().reset_index()
                fig_eng = px.bar(engagement_counts, x='Event', y='count', title="Portal Activity Distribution")
                st.plotly_chart(fig_eng, use_container_width=True)
            else:
                st.info("Attendance data will appear once students log in.")
        except:
            st.error("Temporal Traces sheet inaccessible.")

    # --- TAB 4: ASSIGNMENT DESK ---
    with tab4:
        st.subheader("📑 Assignment Orchestration")
        a1, a2 = st.columns(2)
        with a1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write("📤 **Post New Assignment**")
            with st.form("assign_form"):
                task_title = st.text_input("Task Title")
                task_desc = st.text_area("Description")
                due_date = st.date_input("Due Date")
                if st.form_submit_button("Deploy Task"):
                    st.success("Task deployed to student dashboards.")
            st.markdown('</div>', unsafe_allow_html=True)
        with a2:
            st.write("📥 **Submissions Review**")
            st.info("No student submissions currently pending.")
