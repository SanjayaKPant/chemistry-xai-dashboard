import streamlit as st
import pandas as pd
from openai import OpenAI
from database_manager import get_gspread_client, log_assessment, log_temporal_trace
from datetime import datetime, timedelta

def render_ai_chat(group_name):
    st.markdown("<h2 style='color: #1E3A8A;'>🤖 साथी (Saathi) AI</h2>", unsafe_allow_html=True)
    st.caption("तपाईंको विज्ञान साथी - Your Socratic Science Companion (Grades 8-10)")

    # 1. RETRIEVE RECENT CONTEXT (Research-Critical Step)
    # We pull the last Tier 3 response from session state to 'prime' the AI
    last_q = st.session_state.get('last_question_text', 'a science concept')
    last_ans = st.session_state.get('last_mcq_choice', 'None')
    last_reason = st.session_state.get('last_tier3_reasoning', 'Not provided yet')

    # 2. BILINGUAL ETHICAL DISCLOSURE
    with st.expander("⚖️ रिसर्च र नैतिक खुलासा (Research & Ethical Disclosure)"):
        st.write("""
        - **Saathi AI** ले सिधै उत्तर दिँदैन, यसले तपाईंलाई सोच्न मद्दत गर्दछ।
        - यो कुराकानी तपाईंको सिकाइ प्रक्रिया बुझ्नको लागि रेकर्ड गरिएको छ।
        """)

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "messages" not in st.session_state:
        # Prime the AI with the student's actual reasoning context
        st.session_state.messages = []
        initial_context = f"Student just answered: '{last_q}'. They chose: '{last_ans}'. Their reasoning was: '{last_reason}'."
        st.session_state.messages.append({"role": "system", "content": initial_context})

    # Display Chat
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 3. CHAT INPUT WITH BILINGUAL GUIDANCE
    if prompt := st.chat_input("तपाईंको जिज्ञासा यहाँ लेख्नुहोस् (Write your query here)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # SYSTEM ROLE: Grade 8-10 Socratic Tutor
            system_prompt = f"""
            You are 'Saathi AI' (साथी AI), a Socratic tutor for Grade 8, 9, and 10 students in Nepal.
            
            CONTEXT FOR THIS SESSION:
            - Question: {last_q}
            - Student's Choice: {last_ans}
            - Student's Reasoning: {last_reason}
            
            STRICT SOCRATIC RULES:
            1. NEVER give the answer.
            2. If the student's reasoning ({last_reason}) is wrong, ask a 'Probing Question' to reveal the flaw.
            3. Use simple English and occasionally include Nepali encouraging words (e.g., "राम्रो प्रयास!", "फेरि विचार गर्नुस्").
            4. Keep responses short (under 3 sentences) to suit Grade 8-10 attention spans.
            5. Focus on the science curriculum of Nepal (Mass, Force, Pressure, etc.).
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
                temperature=0.7
            )
            
            ai_reply = response.choices[0].message.content
            st.markdown(ai_reply)
            
            # 4. LOGGING THE TRACE (For Journal Analysis)
            log_temporal_trace(
                st.session_state.user['User_ID'], 
                "SOCRATIC_INTERVENTION", 
                f"Q: {last_q} | Reason: {last_reason} | AI: {ai_reply}"
            )
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
