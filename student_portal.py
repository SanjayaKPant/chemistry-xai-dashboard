import streamlit as st
import pandas as pd
from database_manager import get_gspread_client

def show():
    user_group = st.session_state.user.get('group', 'Control')
    st.title("🎓 Student Learning Portal")

    # DISTINCT UI DIFFERENTIATION
    if user_group == "Exp_A":
        st.sidebar.warning("🔬 INTERACTIVE AI MODE")
        menu = ["📚 Interactive Modules", "🤖 Socratic Tutor", "✍️ 4-Tier Assessment"]
    else:
        st.sidebar.info("📘 STANDARD DIGITAL MODE")
        menu = ["📚 Digital Library", "✍️ 4-Tier Assessment"]
    
    choice = st.sidebar.radio("Navigation", menu)

    if choice in ["📚 Interactive Modules", "📚 Digital Library"]:
        render_learning_path(user_group)
    elif choice == "🤖 Socratic Tutor":
        render_socratic_tutor()
    elif choice == "✍️ 4-Tier Assessment":
        render_assessment()

def render_learning_path(group):
    st.header(f"📂 { 'Interactive Modules' if group == 'Exp_A' else 'Digital Library'}")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        df.columns = df.columns.str.strip()
        
        my_lessons = df[df['Group'] == group]

        if not my_lessons.empty:
            for _, row in my_lessons.iterrows():
                with st.container(border=True):
                    st.subheader(row['Title'])
                    st.write(f"**Objectives:** {row['Learning_Objectives']}")
                    
                    if group == "Exp_A":
                        # EXPERIMENTAL TRIGGER
                        st.info("🤖 AI is ready to discuss this concept.")
                        if st.button(f"Analyze Reasoning: {row['Title']}"):
                            st.session_state.current_pivot = row['Description']
                            st.write("Redirecting to Socratic Tutor...")
                    else:
                        # CONTROL STATIC LINK
                        st.markdown(f"🔗 [Open Study Material]({row['File_Link']})")
        else:
            st.info("No content assigned yet.")
    except Exception as e:
        st.error(f"Load Error: {e}")

def render_socratic_tutor():
    st.header("🤖 Socratic Tutor")
    # Pull the decision tree logic stored in 'Description'
    pivot_logic = st.session_state.get('current_pivot', "Tell me what you've learned so far.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I'm ready. What is your understanding of the lesson?"}]

    for m in st.session_state.messages:
        st.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # RESEARCH LOGIC: Parsing the decision tree
        # IF: Acids burn | THEN: Is lemon dangerous?
        if "IF:" in pivot_logic and "THEN:" in pivot_logic:
            condition = pivot_logic.split("|")[0].replace("IF:", "").strip().lower()
            response = pivot_logic.split("|")[1].replace("THEN:", "").strip()
            
            if condition in prompt.lower():
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Interesting. Can you elaborate more on that?"})
        
        st.rerun()

def render_assessment():
    st.header("✍️ 4-Tier Diagnostic")
    with st.form("quiz"):
        st.write("Standard Assessment Logic Here...")
        if st.form_submit_button("Submit"):
            st.success("Logged.")
