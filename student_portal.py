import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

# --- HELPERS ---
def get_nepal_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

def show():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.warning("Please login first!")
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

# --- 1. MODULES WITH "REVISION MODE" (TIERS 5 & 6) ---
def render_modules(student_group):
    st.title("📚 Learning Modules")
    
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Instructional_Materials").get_all_records())
        modules = df[df['Group'] == student_group]
        
        for idx, row in modules.iterrows():
            st.markdown(f"### 📖 {row['Sub_Title']}")
            
            # Check if student already submitted Tier 1-4
            is_revision = st.session_state.get(f"revizing_{row['Sub_Title']}", False)

            if not is_revision:
                # --- STANDARD 4-TIER START ---
                st.write(f"**Question:** {row['Diagnostic_Question']}")
                ans = st.radio(f"Tier 1: सही उत्तर (Answer)", [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']], key=f"t1_{idx}")
                conf1 = st.select_slider(f"Tier 2: आत्मविश्वास (Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t2_{idx}")
                reason = st.text_area(f"Tier 3: वैज्ञानिक तर्क (Reasoning)", key=f"t3_{idx}")
                conf2 = st.select_slider(f"Tier 4: तर्कमा विश्वास (Reasoning Confidence)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t4_{idx}")

                if st.button("Submit First Thought", key=f"btn_{idx}"):
                    log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], ans, conf1, reason, conf2, "INITIAL", get_nepal_time())
                    st.session_state.last_question_text = row['Diagnostic_Question']
                    st.session_state.last_tier3_reasoning = reason
                    st.success("Now, go to साथी (Saathi) AI to discuss your logic!")
            else:
                # --- REVISION MODE (TIERS 5 & 6) ---
                st.info("🎯 **साथी AI सँगको छलफल पछि आफ्नो तर्क परिमार्जन गर्नुहोस्।** (Refine your reasoning after Saathi AI discussion.)")
                st.write(f"**Original Question:** {row['Diagnostic_Question']}")
                st.write(f"**Your Previous Reason:** {st.session_state.get('last_tier3_reasoning')}")
                
                rev_reason = st.text_area("Tier 5: परिमार्जित वैज्ञानिक तर्क (Revised Scientific Reasoning)", key=f"t5_{idx}")
                rev_conf = st.select_slider("Tier 6: नयाँ आत्मविश्वास (New Confidence Level)", options=["Guessing", "Unsure", "Sure", "Very Sure"], key=f"t6_{idx}")

                if st.button("Submit Final Mastery", key=f"rev_btn_{idx}"):
                    log_assessment(st.session_state.user['User_ID'], student_group, row['Sub_Title'], "REVISED", "REVISED", rev_reason, rev_conf, "MASTERY", get_nepal_time())
                    st.balloons()
                    st.success("Mastery Logged! Check 'My Progress' to see your growth.")
                    st.session_state[f"revizing_{row['Sub_Title']}"] = False
            st.divider()
    except Exception as e:
        st.error(f"Error: {e}")

# --- 2. SAATHI AI WITH MASTERY TAGGING ---
def render_ai_chat(group_name):
    st.header("🤖 साथी (Saathi) AI")
    last_reason = st.session_state.get('last_tier3_reasoning', '')
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": f"Student reasoning to probe: {last_reason}. Focus on Grade 8-10 curriculum. Use Socratic questions."}]

    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask Saathi AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "If student shows mastery, end with [MASTERY_REACHED]."}] + st.session_state.messages
            )
            ai_reply = response.choices[0].message.content
            
            # LOG BOTH SIDES
            log_temporal_trace(st.session_state.user['User_ID'], "DIALOGUE", f"U: {prompt} | AI: {ai_reply}")
            
            if "[MASTERY_REACHED]" in ai_reply:
                st.markdown(ai_reply.replace("[MASTERY_REACHED]", ""))
                st.session_state[f"revizing_{st.session_state.get('current_topic')}"] = True
                st.success("साथी AI believes you are ready to revise your answer! Go to 'Learning Modules'.")
            else:
                st.markdown(ai_reply)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})

# --- 3. THE METACOGNITIVE PROGRESS DASHBOARD ---
def render_metacognitive_dashboard(uid):
    st.title("📈 मेरो प्रगति (My Progress)")
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1UqWkZKJdT2CQkZn5-MhEzpSRHsKE4qAeA17H0BOnK60")
        df = pd.DataFrame(sh.worksheet("Assessment_Logs").get_all_records())
        user_data = df[df['User_ID'].astype(str) == str(uid)]

        if user_data.empty:
            st.info("No data yet.")
            return

        # Map confidence for visualization
        c_map = {"Guessing": 1, "Unsure": 2, "Sure": 3, "Very Sure": 4}
        user_data['conf_numeric'] = user_data['Tier_2 (Confidence_Ans)'].map(c_map)

        # Plotly Calibration Chart
        st.subheader("Your Confidence over Time")
        fig = px.line(user_data, x="Timestamps", y="conf_numeric", markers=True, 
                     title="Metacognitive Growth Line", labels={"conf_numeric": "Confidence Level"})
        st.plotly_chart(fig)
        
    except Exception as e:
        st.error(f"Error: {e}")

def render_dashboard(user):
    st.title(f"Namaste, {user['Name']}! 🙏")
    st.write("Welcome to your Socratic Science journey.")
