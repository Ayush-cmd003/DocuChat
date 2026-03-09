import json
import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import uuid

from utils.security import encrypt_key, decrypt_key

SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

def initialize_cookies():
    cookie_password = os.getenv("COOKIE_SECRET") or st.secrets.get("COOKIE_SECRET")

    if not cookie_password:
        st.error("COOKIE_SECRET is not configured")
        st.stop()

    # Create cookie manager only once
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = EncryptedCookieManager(
            prefix="docuchat_",
            password=cookie_password
        )

    cookies = st.session_state.cookie_manager

    if not cookies.ready():
        st.stop()

    if "session_id" not in cookies:
        cookies["session_id"] = str(uuid.uuid4())
        cookies.save()

    st.session_state.session_id = cookies["session_id"]
    cookie_password = os.getenv("COOKIE_SECRET")

    if not cookie_password:
        st.error("COOKIE_SECRET environment variable is not set.")
        st.stop()

    cookies = EncryptedCookieManager(
        prefix="docuchat_",
        password=cookie_password
    )

    if not cookies.ready():
        st.stop()

    if "session_id" not in cookies:
        cookies["session_id"] = str(uuid.uuid4())
        cookies.save()

    st.session_state.session_id = cookies["session_id"]
    cookie_password = os.getenv("COOKIE_SECRET")
    cookies = EncryptedCookieManager(prefix="docuchat_", password=cookie_password)
    if not cookies.ready():
        st.stop()

    if "session_id" not in cookies:
        cookies["session_id"] = str(uuid.uuid4())
        cookies.save()

    st.session_state.session_id = cookies["session_id"]

def get_session_file():
    session_id = st.session_state.get("session_id")

    if not session_id:
        return None

    return os.path.join(
        SESSION_DIR,
        f"session_{session_id}.json"
    )

def save_session():
    api_key = st.session_state.get("api_key")
    encrypted_key = encrypt_key(api_key) if api_key else None
    data = {
        "api_key": encrypted_key,
        "key_valid": st.session_state.get("key_valid"),
        "chats": st.session_state.get("chats"),
        "chat_order": st.session_state.get("chat_order"),
        "current_chat": st.session_state.get("current_chat"),
        "active_files": list(st.session_state.get("active_files", []))
    }

    with open(get_session_file(), "w") as f:
        json.dump(data, f)


def load_session():
    session_file = get_session_file()

    if not session_file or not os.path.exists(session_file):
        return

    with open(session_file, "r") as f:
        data = json.load(f)

    encrypted_key = data.get("api_key")

    if encrypted_key:
        st.session_state.api_key = decrypt_key(encrypted_key)
        st.session_state.key_valid = True
    else:
        st.session_state.key_valid = False

    st.session_state.chats = data.get("chats", {})
    st.session_state.chat_order = data.get("chat_order", [])
    st.session_state.current_chat = data.get("current_chat")
    st.session_state.active_files = set(data.get("active_files", []))