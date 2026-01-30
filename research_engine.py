import streamlit as st
from datetime import datetime

def log_temporal_trace(event_type, details=""):
    """Captures micro-timestamps for Process Mining (Theme 9)."""
    if "trace_buffer" not in st.session_state:
        st.session_state.trace_buffer = []
    
    trace_entry = {
        "User_ID": st.session_state.user_data.get('User_ID', 'Guest'),
        "Timestamp": datetime.now().isoformat(),
        "Event": event_type,
        "Details": details
    }
    st.session_state.trace_buffer.append(trace_entry)

def get_agentic_hint(misconception_key):
    """Socratic Companion Agent for Conceptual Reframing."""
    log_temporal_trace("AGENT_INTERVENTION", details=misconception_key)
    hints = {
        "NUCLEUS_ERROR": "🤖 Agent: If electrons are inside the nucleus, how would they maintain orbits? Reflect on Rutherford's findings.",
        "BOND_ERROR": "🤖 Agent: Atoms seek minimum energy. Is it easier to gain 7 electrons or lose 1 to reach stability?"
    }
    return hints.get(misconception_key, "🤖 Agent: Re-examine the sub-microscopic particles involved.")