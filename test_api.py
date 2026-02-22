import google.generativeai as genai
import streamlit as st

# Use your existing secret
genai.configure(api_key=st.secrets["AIzaSyAj1MP0ArtogiRhMw_jzYaZA7a0U2H6ky0"])

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Available Model: {m.name}")
            st.write(f"✅ Your API supports: {m.name}")
except Exception as e:
    st.error(f"API Key Error: {e}")
