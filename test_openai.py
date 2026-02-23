import streamlit as st
from openai import OpenAI

st.title("🧪 OpenAI Connection Test")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Key not found in Streamlit Secrets!")
else:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    if st.button("Test API Connection"):
        try:
            # A tiny, 5-token request to verify the key is active
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Use mini for testing to save money
                messages=[{"role": "user", "content": "Say 'Connection Successful'"}],
                max_tokens=5
            )
            st.success(response.choices[0].message.content)
            st.balloons()
        except Exception as e:
            st.error(f"Connection Failed: {e}")
            if "insufficient_quota" in str(e):
                st.warning("Wait 5-10 minutes for your $5.00 payment to propagate.")
