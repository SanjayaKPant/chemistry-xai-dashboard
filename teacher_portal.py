import streamlit as st
import pandas as pd
import plotly.express as px
from database_manager import save_bulk_concepts, upload_to_drive, get_gspread_client, save_assignment

def show():
    user = st.session_state.user
    
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab"] { font-weight: bold; padding: 10px 20px; }
        .deployment-card { 
            background-color: #ffffff; padding: 20px; border-radius: 12px;
            border-left: 5px solid #007bff; box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧑‍🏫 LMS Orchestration & Research Hub")
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Deployment Center", "📊 Learning Analytics", "📈 Engagement", "📑 Assignments"])

    # --- TAB 1: DEPLOYMENT ---
    with tab1:
        st.subheader("Deploy New Learning Module")
        with st.form("professional_lesson_form"):
            col1, col2 = st.columns([1, 2])
            target_group = col1.selectbox("Target Research Group", ["School A", "School B"])
            main_title = col2.text_input("Chapter Title", placeholder="e.g., Classification of Elements")
            
            sub_title = st.text_input("Specific Concept Name", placeholder="e.g., Modern Periodic Law")
            objectives = st.text_area("Learning Objectives", height=70)

            st.write("---")
            st.write("📦 Resources & Multi-Tier Assessment")
            up_files = st.file_uploader("Upload Textbook Pages/Images (Multiple)", accept_multiple_files=True)
            vid_url = st.text_input("Video Resource URL")
            
            q_text = st.text_area("Diagnostic Question (Tier 1)")
            c1, c2 = st.columns(2)
            oa = c1.text_input("Option A")
            ob = c2.text_input("Option B")
            oc = c1.text_input("Option C")
            od = c2.text_input("Option D")
            correct = st.selectbox("Correct Key", ["A", "B", "C", "D"])
            
            socratic_logic = st.text_area("🧠 Socratic Tree (Scaffolding logic for School A)")

            if st.form_submit_button("🚀 DEPLOY TO PORTALS"):
                with st.spinner("Uploading assets and syncing database..."):
                    # Handle multiple files
                    links = [upload_to_drive(f) for f in up_files] if up_files else []
                    file_string = ", ".join(links)
                    
                    data_package = {
                        "sub_title": sub_title, "objectives": objectives,
                        "file_link": file_string, "video_link": vid_url,
                        "q_text": q_text, "oa": oa, "ob": ob, "oc": oc, "od": od,
                        "correct": correct, "socratic_tree": socratic_logic
                    }
                    
                    if save_bulk_concepts(user['User_ID'], target_group, main_title, data_package):
                        st.success(f"Module '{sub_title}' is now live for {target_group}!")
                        st.balloons()

    # --- TAB 2: ANALYTICS ---
    with tab2:
        st.header("Assessment Data Visualization")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
            if not df.empty:
                fig = px.histogram(df, x="Tier_2", color="Group", barmode="group",
                                   title="Student Confidence Distribution (Tier 2)")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No assessment logs found yet.")
        except:
            st.error("Could not reach Assessment_Logs sheet.")

    # --- TAB 3: ENGAGEMENT ---
    with tab3:
        st.header("Temporal Engagement Traces")
        try:
            client = get_gspread_client()
            sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
            traces_df = pd.DataFrame(sh.worksheet("Temporal_Traces").get_all_records())
            if not traces_df.empty:
                fig_activity = px.pie(traces_df, names='Event', title="Portal Interaction Spread")
                st.plotly_chart(fig_activity, use_container_width=True)
            else:
                st.info("No engagement data collected yet.")
        except:
            st.error("Error loading Engagement Traces.")

    # --- TAB 4: ASSIGNMENTS ---
    with tab4:
        st.header("📑 Assignment Management")
        with st.form("teacher_assign_form"):
            a_title = st.text_input("Task Title")
            a_group = st.selectbox("Assign To", ["School A", "School B"], key="ta_grp")
            a_desc = st.text_area("Detailed Instructions")
            a_file = st.file_uploader("Upload Reference PDF")
            
            if st.form_submit_button("Post Assignment"):
                f_url = upload_to_drive(a_file) if a_file else ""
                if save_assignment(user['User_ID'], a_group, a_title, a_desc, f_url):
                    st.success("Assignment deployed and saved to Drive.")
