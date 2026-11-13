"""Small session-memory helpers for Streamlit state."""
import streamlit as st


def init_memory():
    defaults = {"selected_doc_id": None, "conversation": [], "viva_session": None, "selected_difficulty": "Intermediate"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_turn(question, answer, doc_id):
    st.session_state.conversation.append({"question": question, "answer": answer, "doc_id": doc_id})
