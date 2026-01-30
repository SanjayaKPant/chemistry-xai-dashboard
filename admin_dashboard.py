import streamlit as st
import pandas as pd

def show_admin_portal(conn):
    st.title("📊 Research Management Console")
    
    tab1, tab2 = st.tabs(["Static Responses", "High-Fidelity Temporal Traces"])
    
    with tab1:
        st.subheader("Standard 4-Tier Data")
        if st.button("Fetch Response Data"):
            data = conn.read(worksheet="Responses", ttl=0)
            st.dataframe(data)
            st.download_button("Download CSV", data.to_csv(index=False).encode('utf-8'), "responses.csv")

    with tab2:
        st.subheader("Process Mining Export")
        st.write("Contains every second of student interaction for **Reflection Latency** analysis.")
        if st.button("Generate Trace Report"):
            if "trace_buffer" in st.session_state:
                df_traces = pd.DataFrame(st.session_state.trace_buffer)
                st.dataframe(df_traces)
                st.download_button("Download Traces (CSV)", df_traces.to_csv(index=False).encode('utf-8'), "temporal_traces.csv")
            else:
                st.warning("No active session traces found.")