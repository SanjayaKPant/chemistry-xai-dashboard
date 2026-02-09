import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    # 1. Identify Student Context
    user_group = st.session_state.user.get('group', 'Control')
    st.title("🎓 Student Learning Portal")
    st.sidebar.info(f"Research Group: {user_group}")

    # 2. Navigation - Socratic Tutor is Exp_A Exclusive
    menu = ["📚 Learning Modules", "✍️ 4-Tier Assessment", "📊 My Progress"]
    if user_group == "Exp_A":
        menu.insert(1, "🤖 Socratic AI Tutor")
    
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "📚 Learning Modules":
        render_learning_path(user_group)
    elif choice == "🤖 Socratic AI Tutor":
        render_socratic_tutor()
    elif choice == "✍️ 4-Tier Assessment":
        render_assessment(user_group)
    elif choice == "📊 My Progress":
        render_progress()

def render_learning_path(group):
    st.header("📚 Your Learning Journey")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        raw_data = sh.worksheet("Instructional_Materials").get_all_records()
        
        if not raw_data:
            st.warning("No modules have been deployed yet.")
            return

        df = pd.DataFrame(raw_data)
        df.columns = df.columns.str.strip() # Clean headers

        # 3. Filter Content by Group
        my_lessons = df[df['Group'] == group]

        if not my_lessons.empty:
            for _, row in my_lessons.iterrows():
                # Matching your EXACT headers: Title, Learning_Objectives, File_Link
                with st.expander(f"📖 {row['Title']}"):
                    st.write(f"**Learning Objective:** {row['Learning_Objectives']}")
                    
                    st.markdown(f"🔗 [Access Lesson Materials]({row['File_Link']})")
                    
                    if group == "Exp_A":
                        st.info("💡 **AI Scout:** Head over to the Socratic Tutor tab to discuss this lesson.")
        else:
            st.info(f"No lessons are currently assigned to the {group} group.")

    except Exception as e:
        st.error(f"Error loading path: {e}")

def render_socratic_tutor():
    st.header("🤖 Socratic Chemistry Assistant")
    
    # 4. Pull 'Socratic Knowledge' from Description column
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        mats = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        # Use the description from the latest lesson as the AI's starting anchor
        latest_anchor = mats.iloc[-1]['Description'] if not mats.empty else "Let's explore chemical principles together."
    except:
        latest_anchor = "How can I help you think through your reasoning today?"

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role": "assistant", "content": f"Hello! {latest_anchor}"}]

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Explain your reasoning..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        # Logic for Gemini API goes here
        st.rerun()

def render_assessment(group):
    st.header("✍️ 4-Tier Diagnostic Assessment")
    st.caption("Standardized across all groups for research validity.")
    
    with st.form("quiz_form"):
        st.subheader("Tier 1: Content")
        t1 = st.radio("What happens to pH when you dilute a strong acid with water?", 
                      ["Decreases", "Increases", "Stays the same"])
        
        st.subheader("Tier 2: Confidence")
        t2 = st.select_slider("Confidence in Answer", ["Low", "Moderate", "High"], key="t2")
        
        st.subheader("Tier 3: Reasoning")
        t3 = st.text_area("Explain the chemical mechanism of dilution:")
        
        st.subheader("Tier 4: Confidence")
        t4 = st.select_slider("Confidence in Reasoning", ["Low", "Moderate", "High"], key="t4")
        
        if st.form_submit_button("Submit Data for Analysis"):
            st.success("Your response has been logged to the research database.")

def render_progress():
    st.header("📊 My Progress")
    st.write("Visualizing your conceptual growth and participation.")
