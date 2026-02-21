import streamlit as st
from database_manager import save_bulk_concepts, upload_to_drive

def show():
    user = st.session_state.user
    
    # Custom CSS for Professional Branding
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stButton>button { 
            background-color: #007bff; color: white; border-radius: 8px; 
            width: 100%; border: none; height: 3em; font-weight: bold;
        }
        .stTextInput>div>div>input { border-radius: 5px; }
        .stTextArea>div>div>textarea { border-radius: 5px; }
        .deployment-card { 
            background-color: #ffffff; padding: 20px; border-radius: 15px;
            border-left: 5px solid #007bff; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧑‍🏫 Research Orchestration Dashboard")
    st.markdown("---")

    with st.container():
        st.markdown('<div class="deployment-card">', unsafe_allow_html=True)
        with st.form("professional_lesson_form"):
            # ROW 1: Compact Group & Large Concept
            r1_col1, r1_col2, r1_col3 = st.columns([1, 1.5, 1.5])
            with r1_col1:
                target_group = st.selectbox("Assign Group", ["School A", "School B"], help="Select target research group")
            with r1_col2:
                main_title = st.text_input("Chapter Title", "Classification of Elements")
            with r1_col3:
                sub_title = st.text_input("Atomic Concept", placeholder="e.g. Modern Periodic Law")

            # ROW 2: Massive Objectives Field
            objectives = st.text_area("🎯 Learning Objectives & Outcomes", height=100)

            st.markdown("🚀 **Diagnostic Design (4-Tier Ready)**")
            
            
            # ROW 3: The Question
            q_text = st.text_input("Diagnostic Question (Tier 1)", placeholder="Enter the central research question here...")

            # ROW 4: Options and Answer (Compact Grid)
            o1, o2, o3, o4, ans = st.columns([1, 1, 1, 1, 0.8])
            with o1: oa = st.text_input("Option A", "A)")
            with o2: ob = st.text_input("Option B", "B)")
            with o3: oc = st.text_input("Option C", "C)")
            with o4: od = st.text_input("Option D", "D)")
            with ans: correct = st.selectbox("Correct", ["A", "B", "C", "D"])

            st.markdown("📂 **Multimodal Assets & Socratic Logic**")
            
            # ROW 5: Asset Uploads in same row (Miniaturized)
            a1, a2 = st.columns(2)
            with a1:
                up_file = st.file_uploader("Textbook PDF/Image", type=['pdf', 'png', 'jpg'], label_visibility="collapsed")
                st.caption("📄 Upload Textbook Page")
            with a2:
                vid_url = st.text_input("Video URL", placeholder="YouTube/Web Link", label_visibility="collapsed")
                st.caption("🎥 Video Resource Link")

            # ROW 6: Socratic Tree
            socratic_logic = st.text_area("🧠 Socratic Scaffolding Tree (For School A Gemini)", height=80, 
                                          placeholder="If student says X, guide them to Y using Z...")

            if st.form_submit_button("🚀 DEPLOY TO RESEARCH DATABASE"):
                with st.spinner("Processing High-Fidelity Sync..."):
                    # 1. Asset Management
                    file_url = upload_to_drive(up_file) if up_file else ""
                    
                    # 2. Package Data
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
