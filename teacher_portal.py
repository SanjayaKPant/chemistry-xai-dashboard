import streamlit as st
from database_manager import check_login, upload_and_log_material, get_materials_by_group

def show():
    st.title("🧑‍🏫 Teacher Command Center")
    
    # Ensure target_group exists before the UI renders
    if 'target_group' not in st.session_state:
        st.session_state.target_group = "Exp_A"
        
    # Rest of your teacher portal code...
    
    # Sidebar for targeting specific experimental groups
    st.sidebar.header("Targeting")
    selected_group = st.sidebar.selectbox("Target Class Group", ["Exp_A", "Exp_B", "Control"])
    
    st.markdown("### 📚 Instructional Material Design")
    st.write("Upload materials to personalize the learning path for your students.")

    with st.form("teacher_upload_form", clear_on_submit=True):
        title = st.text_input("Lesson Title (e.g., The Bohr Model)")
        mode = st.radio("Instructional Track", ["Traditional (Control)", "AI-Integrated (Experimental)"])
        
        # Direct PDF Upload
        pdf_file = st.file_uploader("Upload Instructional PDF", type=['pdf'])
        
        desc = st.text_area("Detailed Learning Objectives / Task Instructions")
        
        # High Refinement AI Hint for personalized feedback
        ai_hint = ""
        if mode == "AI-Integrated (Experimental)":
            ai_hint = st.text_input("AI Scaffolding Hint (e.g., 'Target misconceptions about electron shells')")

        submit = st.form_submit_button("🚀 Publish & Systematize")

        if submit:
            if title and pdf_file:
                with st.spinner("Processing file and updating research database..."):
                    success = upload_and_log_material(
                        user['id'], 
                        selected_group, 
                        title, 
                        mode, 
                        pdf_file, 
                        desc, 
                        ai_hint
                    )
                    
                    if success:
                        log_temporal_trace(user['id'], f"Published {title} to {selected_group}")
                        st.success(f"✅ Lesson '{title}' is now live for group {selected_group}!")
                    else:
                        st.error("Failed to publish. Check tab names in Google Sheets.")
            else:
                st.error("Please provide both a Lesson Title and a PDF file.")

    # Inside your teacher view function:
st.divider()
st.subheader("📊 Previously Published Materials")
all_materials = get_materials_by_group(st.session_state.target_group)

if all_materials:
    df_display = pd.DataFrame(all_materials)
    # Only show relevant columns to the teacher
    st.table(df_display[['Timestamp', 'Title', 'Mode', 'File_Link']])
else:
    st.write("No materials found for this group.")

st.subheader("📊 Previously Published Materials")
# This uses the session_state we just initialized!
history = get_materials_by_group(st.session_state.target_group) 

if history:
    for item in history:
        with st.expander(f"📁 {item['Title']}"):
            st.link_button("Open Original PDF", item['File_Link'])
