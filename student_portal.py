import streamlit as st
import pandas as pd
import google.generativeai as genai
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
import plotly.express as px

# --- RESEARCH-GRADE SOCRATIC SYSTEM PROMPT ---
SOCRATIC_PROMPT = """
You are a Socratic Chemistry Tutor designed for Grade 10 students in Nepal. 
Your goal is to guide students toward conceptual clarity using the National Curriculum standards.

SCIENTIFIC APPROACH:
1. Ground questions in molecular behavior, periodic trends (Modern Periodic Law), and sub-shell electronic configuration (Aufbau's Principle).
2. Address specific textbook concepts: Metals/Non-metals, Alkali/Alkaline Earth metals, and Halogens.
3. Scaffolding: Use the 'Socratic_Tree' guidance from the teacher to identify logical hurdles.

ETHICAL GUIDELINES:
- Never provide the final answer or chemical formulas directly.
- Use encouraging language to reduce 'Science Anxiety'.
"""

# --- AI SETUP ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')

def show():
    user = st.session_state.user
    user_school = str(user.get('Group', 'School B')).strip()
    
    st.sidebar.markdown(f"## 🎓 {user.get('Name')}")
    st.sidebar.info(f"Group: {user_school}")
    
    menu = ["🏠 Dashboard", "📚 Learning Modules", "🤖 Socratic AI Chat", "📈 My Progress"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "🏠 Dashboard":
        render_dashboard(user)
    elif choice == "📚 Learning Modules":
        render_learning_modules(user_school)
    elif choice == "🤖 Socratic AI Chat":
        render_socratic_chat()
    elif choice == "📈 My Progress":
        render_visual_progress(user.get('User_ID'))

def render_dashboard(user):
    st.title(f"Chemistry Learning Hub 👋")
    st.subheader("🏁 Learning Progress Indicator")
    # Simulation of progress tracker
    st.progress(0.4) 
    st.caption("You have completed 40% of the assigned curriculum. Great job!")
    
    st.markdown("---")
    st.markdown("### 📝 My Assignments")
    st.write("✅ Modern Periodic Law Quiz")
    st.write("⏳ Sub-shell Configuration (Due Friday)")

def render_learning_modules(school):
    st.header("📚 Digital Lessons")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        data = sh.worksheet("Instructional_Materials").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = [c.strip().upper() for c in df.columns]
        my_lessons = df[df['GROUP'].str.strip().str.upper() == school.upper()]

        for idx, row in my_lessons.iterrows():
            with st.expander(f"📖 {row['SUB_TITLE']}", expanded=True):
                # 2. ATTACHMENTS JUST BELOW OBJECTIVES
                st.info(f"🎯 **Objective:** {row['LEARNING_OBJECTIVES']}")
                c1, c2 = st.columns(2)
                with c1:
                    if row['FILE_LINKS']: st.link_button("📄 Textbook Page (PDF)", row['FILE_LINKS'], use_container_width=True)
                with c2:
                    if row['VIDEO_LINKS']: st.link_button("🎥 Video Resource", row['VIDEO_LINKS'], use_container_width=True)
                
                st.markdown("---")
                # 5. 4-TIER ASSESSMENT
                st.subheader("🧪 4-Tier Diagnostic Question")
                st.write(row['DIAGNOSTIC_QUESTION'])
                with st.form(key=f"form_{idx}"):
                    t1 = st.radio("Select Answer", [row['OPTION_A'], row['OPTION_B'], row['OPTION_C'], row['OPTION_D']])
                    t2 = st.select_slider("Confidence in Answer", ["Unsure", "Sure", "Very Sure"])
                    t3 = st.text_area("Why did you choose this? (Reasoning)")
                    t4 = st.select_slider("Confidence in Reasoning", ["Unsure", "Sure", "Very Sure"])
                    
                    if st.form_submit_button("Submit & Unlock Chat"):
                        log_assessment(st.session_state.user['User_ID'], school, row['SUB_TITLE'], t1, t2, t3, t4, "Logged", "N/A")
                        # Store context for Socratic Chat
                        st.session_state.current_topic = row['SUB_TITLE']
                        st.session_state.teacher_tree = row['SOCRATIC_TREE']
                        st.success("Responses Saved! Go to 'Socratic AI Chat' to discuss.")

    except Exception as e:
        st.error(f"Error: {e}")

def render_socratic_chat():
    st.header("🤖 Socratic Chemistry Tutor")
    if 'current_topic' not in st.session_state:
        st.warning("Please complete a Diagnostic Question in 'Learning Modules' first.")
        return

    topic = st.session_state.current_topic
    tree = st.session_state.teacher_tree
    
    st.info(f"Currently discussing: **{topic}**")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"I see you've shared your thoughts on {topic}. Let's explore your reasoning. Why do you think that specific answer fits?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Explain your logic..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Build Research Context
        context = f"Topic: {topic}. Teacher's Scaffolding Plan: {tree}. Student input: {prompt}."
        
        response = model.generate_content(context)
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        log_temporal_trace(st.session_state.user['User_ID'], "SOCRATIC_CHAT", topic)

def render_visual_progress(uid):
    st.header("📈 My Learning Journey")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        logs = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_logs = logs[logs['User_ID'].astype(str) == str(uid)]
        if not user_logs.empty:
            fig = px.line(user_logs, x="Timestamp", y="Tier_2", title="My Confidence Growth", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet. Complete a module to see your chart!")
    except:
        st.error("Progress tracker offline.")
