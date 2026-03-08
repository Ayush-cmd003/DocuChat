import streamlit as st
import uuid
from prompts.welcome_prompt import WELCOME_MESSAGE


def initialize_session():

    if "key_valid" not in st.session_state:
        st.session_state.key_valid = False

    if "api_key" not in st.session_state:
        st.session_state.api_key = None

    if "chats" not in st.session_state:
        st.session_state.chats = {}

    if "chat_order" not in st.session_state:
        st.session_state.chat_order = []

    if "current_chat" not in st.session_state:
        st.session_state.current_chat = None


def create_new_chat():

    chat_id = f"chat_{uuid.uuid4().hex[:8]}"

    messages = []

    if st.session_state.get("key_valid", False):
        messages.append(("assistant", WELCOME_MESSAGE))

    st.session_state.chats[chat_id] = {
        "messages": messages,
        "title": "New Chat"
    }

    st.session_state.chat_order.insert(0, chat_id)
    st.session_state.current_chat = chat_id