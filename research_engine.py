import streamlit as st

def get_agentic_hint(question_id, student_answer):
    hints = {
        "atom_structure_01": {
            "Inside the Nucleus": "If electrons were inside, how would that affect the atom's size compared to Rutherford's findings?",
            "In the Electron Cloud": "Correct! How does distance from the nucleus affect the energy of these electrons?"
        }
    }
    user_data = st.session_state.get('user_data', {})
    if user_data.get('Group') == "Exp_A":
        return hints.get(question_id, {}).get(student_answer)
    return None
