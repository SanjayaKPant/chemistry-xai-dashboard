import streamlit as st
from datetime import datetime

def log_temporal_trace(event_name, details=""):
    """Captures micro-moments for Process Mining."""
    if 'trace_buffer' not in st.session_state:
        st.session_state.trace_buffer = []
    
    trace = {
        "User_ID": st.session_state.user_data.get('User_ID', 'Unknown'),
        "Timestamp": datetime.now().isoformat(),
        "Event": event_name,
        "Details": details
    }
    st.session_state.trace_buffer.append(trace)

def get_agentic_hint(question_id, student_answer):
    """
    The Socratic Heart: Detects misconceptions and returns 
    a 'nudge' instead of the answer.
    """
    hints = {
        "atom_structure_01": {
            "Nucleus": "Interesting! If the electrons were *inside* the nucleus with the protons, how would that affect the overall size of the atom compared to what we observe in Rutherford's experiment?",
            "Electron Cloud": "Correct! You've identified the region. How does the distance from the nucleus affect the energy of these electrons?"
        }
    }
    
    # Logic: Only give hints if the student is in the Experimental Group
    group = st.session_state.user_data.get('Group', 'Control')
    
    if group == "Exp_A": # Socratic Group
        return hints.get(question_id, {}).get(student_answer, None)
    return None
