# ==============================================================
# IMPORT LIBRARIES
# ==============================================================

import streamlit as st
from langchain_groq import ChatGroq

from prompts.welcome_prompt import WELCOME_MESSAGE
from services.embeddings import load_embeddings
from services.vector_store import load_vector_store, add_documents
from services.document_loader import extract_text
from services.llm_service import create_llm

from utils.chat_manager import initialize_session, create_new_chat
from config.settings import TOP_K, MODEL_NAME

from prompts.system_prompt import SYSTEM_PROMPT
from prompts.instructions_prompt import SETUP_INSTRUCTIONS

from utils.style_loader import load_css
import json
import streamlit.components.v1 as components
from config.settings import MAX_FILE_SIZE_MB

import os
from utils.session_data import initialize_cookies, load_session, save_session, get_session_file

import hashlib
import shutil
from config.settings import VECTOR_DB_PATH

from dotenv import load_dotenv

load_dotenv()

def get_file_hash(file):
    return hashlib.md5(file.getvalue()).hexdigest()

# ==============================================================
# PAGE CONFIG
# ==============================================================

st.set_page_config(
    page_title="DocuChat",
    page_icon="assets/favicon.ico",
    layout="wide"
)

load_css("styles/main.css")


st.markdown(
        "<h1 style='margin-bottom:0;'> DocuChat</h1>",
        unsafe_allow_html=True
)

st.markdown(
    "<p style='color:gray;margin-top:0;'>Ask questions about your documents using AI</p>",
    unsafe_allow_html=True
)

st.divider()

# ==============================================================
# SESSION STATE INITIALIZATION
# ==============================================================

initialize_cookies()

if "session_loaded" not in st.session_state:
    load_session()
    st.session_state.session_loaded = True

initialize_session()

if "vector_path" not in st.session_state:
    st.session_state.vector_path = os.path.join(
        VECTOR_DB_PATH,
        f"session_{st.session_state.session_id}"
    )

os.makedirs(st.session_state.vector_path, exist_ok=True)

if "active_files" not in st.session_state:
    st.session_state.active_files = set()

if not st.session_state.chats:
    create_new_chat()

if st.session_state.current_chat not in st.session_state.chats:
    create_new_chat()

chat = st.session_state.chats[st.session_state.current_chat]
messages = chat["messages"]


# ==============================================================
# LOAD EMBEDDINGS
# ==============================================================

# Clean vector database on server restart
if "db_initialized" not in st.session_state:

    if os.path.exists(VECTOR_DB_PATH):
        shutil.rmtree(VECTOR_DB_PATH, ignore_errors=True)

    st.session_state.db_initialized = True

with st.spinner("🔎 Loading embedding model..."):
    embeddings = load_embeddings()

# ==============================================================
# LOAD VECTOR DATABASE
# ==============================================================

if st.session_state.get("vector_store") is None:
    with st.spinner("📚 Loading document database..."):
        st.session_state.vector_store = load_vector_store(embeddings)

# ==============================================================
# SIDEBAR
# ==============================================================

with st.sidebar:

    st.markdown("## 📂 Documents")

    disable_buttons = not st.session_state.key_valid

    files = st.file_uploader(
        "Upload PDF or DOCX",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        disabled=disable_buttons
    )

    current_files = [file.name for file in files] if files else []

    for f in list(st.session_state.active_files):

        if f not in current_files:

            # remove file from active list
            st.session_state.active_files.discard(f)

            # remove its embeddings from vector store
            if "vector_store" in st.session_state and st.session_state.vector_store:

                collection = st.session_state.vector_store._collection

                ids = collection.get(
                    where={"source": f}
                )["ids"]

                if ids:
                    collection.delete(ids=ids)

                st.session_state.vector_store.persist()

                # reload vector store so memory index updates
                st.session_state.vector_store = load_vector_store(embeddings)

    if files and st.session_state.key_valid:

        for file in files:

            # File size check
            file_size_mb = file.size / (1024 * 1024)

            if file_size_mb > MAX_FILE_SIZE_MB:
                st.toast(
                    f"❌ {file.name} exceeds {MAX_FILE_SIZE_MB}MB limit",
                    icon="⚠️"
                )
                continue

            # Duplicate file check
            file_hash = get_file_hash(file)

            if file_hash in st.session_state.active_files:
                st.toast(f"{file.name} already uploaded", icon="⚠️")
                continue

            text = extract_text(file)

            if text and text.strip():
                st.session_state.vector_store = add_documents(
                    st.session_state.vector_store,
                    embeddings,
                    text,
                    file.name
                )

                st.session_state.active_files.add(file.name)
                save_session()

    st.divider()

    st.markdown("## ✉️ Chats")

    if st.button("➕ New Chat", use_container_width=True, disabled=disable_buttons):
        create_new_chat()

        save_session()

        st.rerun()

    st.markdown("---")

    st.session_state.chat_order = list(dict.fromkeys(st.session_state.chat_order))

    for chat_id in st.session_state.chat_order:

        chat_item = st.session_state.chats[chat_id]

        label = chat_item["title"]

        if chat_id == st.session_state.current_chat:
            label = f"👉  {label}"

        if st.button(
                label,
                key=f"chat_{chat_id}",
                use_container_width=True,
                disabled=disable_buttons
        ):
            st.session_state.current_chat = chat_id
            st.rerun()


# ==============================================================
# CHAT HEADER
# ==============================================================

if st.session_state.key_valid:

    header_col, delete_col, logout_col = st.columns([0.90, 0.05, 0.05])

    with header_col:
        st.subheader(chat["title"])

    # Delete button
    with delete_col:
        if st.button("", icon=":material/delete:", help="Delete Chat"):
            current = st.session_state.current_chat

            # remove chat
            st.session_state.chat_order.remove(current)
            del st.session_state.chats[current]

            # if other chats exist → switch to the first one
            if len(st.session_state.chat_order) > 0:
                st.session_state.current_chat = st.session_state.chat_order[0]

            # if no chats exist → create a new chat with welcome message
            else:
                create_new_chat()

            st.rerun()

    # Logout button
    with logout_col:
        if st.button("", icon=":material/logout:", help="Use New API Key"):
            session_file = get_session_file()

            if os.path.exists(session_file):
                os.remove(session_file)

            st.session_state.api_key = None
            st.session_state.key_valid = False
            st.session_state.vector_store = None

            st.rerun()

    st.divider()


# ==============================================================
# API KEY SETUP SCREEN
# ==============================================================

if not st.session_state.key_valid:

    st.info("### ⚙️ Setup Required")

    st.markdown(
        f"""
    <div class="setup-card">

    {SETUP_INSTRUCTIONS}

    """,
        unsafe_allow_html=True
    )

    st.markdown("""
    <style>

    .verify-btn button {
        width:100%;
        height:44px;
        border-radius:8px;
        font-weight:600;
        display:flex;
        align-items:center;
        justify-content:center;
        transition:all 0.2s ease-in-out;
    }

    .verify-btn button:hover {
        background-color:#4CAF50;
        color:white;
        border-color:#4CAF50;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="api-card">
    
        <h3>🔑 Enter your Groq API Key</h3>
        <p>
        Your API key is only used to connect DocuChat with Groq.
        </p>
    
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("api_key_form"):

        key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            label_visibility="collapsed"
        )

        verify = st.form_submit_button(
            "Verify Key",
            use_container_width=True
        )

        if verify:

            if not key:
                st.error("Please enter your API key.")

            else:
                try:

                    test_llm = ChatGroq(
                        model=MODEL_NAME,
                        groq_api_key=key,
                        reasoning_format="hidden"
                    )

                    test_llm.invoke("hello")

                    st.session_state.api_key = key
                    st.session_state.key_valid = True

                    if not st.session_state.chats:
                        create_new_chat()
                        st.success("✅ API key verified successfully")
                        st.rerun()
                    else:
                        chat = st.session_state.chats[st.session_state.current_chat]
                        if not chat["messages"]:
                            chat["messages"].append(("assistant", WELCOME_MESSAGE))
                    save_session()
                except Exception:
                    st.error("❌ Invalid Groq API Key")

    st.stop()


# ==============================================================
# DISPLAY CHAT HISTORY
# ==============================================================

for i, message in enumerate(messages):

    role = message[0]
    msg = message[1]
    sources = message[2] if len(message) > 2 else None

    with st.chat_message(role):

        st.markdown(msg)

        if role == "assistant" and sources:

            safe_text = json.dumps(msg)
            source_text = f'<span style="font-size:13px;">📚 <b>File:</b> {", ".join(sources)}</span>'

            button_id = f"copyBtn_{i}"

            components.html(
                f"""
                <div style="display:flex;justify-content:space-between;align-items:center;font-size:13px;margin-top:6px;">

                    <div>{source_text}</div>

                    <button id="{button_id}" 
                    style="border:none;background:none;font-size:16px;cursor:pointer;">
                    📋
                    </button>

                </div>

                <script>
                const textToCopy = {safe_text};
                const btn = document.getElementById("{button_id}");

                btn.onclick = function() {{
                    navigator.clipboard.writeText(textToCopy).then(() => {{
                        btn.innerHTML = "✔️";

                        setTimeout(() => {{
                            btn.innerHTML = "📋";
                        }}, 2000);
                    }});
                }};
                </script>
                """,
                height=40
            )


# ==============================================================
# INITIALIZE LLM
# ==============================================================

llm = None

if st.session_state.api_key:
    llm = create_llm(st.session_state.api_key)


# ==============================================================
# CHAT INPUT
# ==============================================================

question = st.chat_input("Ask something...")


# ==============================================================
# QUESTION ANSWERING LOGIC
# ==============================================================

if question:

    question = question.strip()

    with st.chat_message("user"):
        st.markdown(question)

    messages.append(("user", question))

    save_session()

    if chat["title"] == "New Chat":

        title = question.strip()

        if len(title) > 50:
            title = title[:50].rsplit(" ", 1)[0] + "..."

        chat["title"] = title

        save_session()

    try:

        if question.lower().strip() in ["hello", "hi", "hey"]:

            response = "Hello! 👋 How can I help you with your documents today?"

            with st.chat_message("assistant"):
                st.markdown(response)

            messages.append(("assistant", response))

        elif not st.session_state.active_files:

            response = "No documents are currently uploaded."
            with st.chat_message("assistant"):
                st.markdown(response)
            messages.append(("assistant", response))

        else:

            if not st.session_state.vector_store:
                response = "No documents are currently uploaded."

            results = st.session_state.vector_store.similarity_search(
                question.lower(),
                k=TOP_K
            )

            relevant_docs = results

            sources = list(set(
                doc.metadata.get("source")
                for doc in relevant_docs
                if doc.metadata.get("source")
            ))

            if not relevant_docs:

                response = "The answer was not found in the uploaded documents."

                with st.chat_message("assistant"):
                    st.markdown(response)

                messages.append(("assistant", response))


            else:

                context = "\n\n".join([d.page_content for d in relevant_docs])

                # Build conversation history
                history = ""

                for message in messages[:-1]:

                    role = message[0]
                    msg = message[1]

                    if role == "user":
                        history += f"User: {msg}\n"
                    else:
                        history += f"Assistant: {msg}\n"

                # Create prompt with history
                prompt = (
                        SYSTEM_PROMPT.format(context=context)
                        + "\n\nConversation History:\n"
                        + history
                        + f"\nUser Question: {question}"
                )

                with st.chat_message("assistant"):

                    with st.spinner("🤖 Analyzing your documents..."):

                        response_container = st.empty()
                        full_response = ""
                        thinking = False

                        for chunk in llm.stream(prompt):

                            token = getattr(chunk, "content", "") or ""

                            if "<think>" in token:
                                thinking = True
                                token = token.split("<think>")[0]

                            if "</think>" in token:
                                thinking = False
                                token = token.split("</think>")[-1]

                            if thinking:
                                continue

                            full_response += token

                            # typing effect
                            response_container.markdown(full_response)

                        response_container.markdown(full_response)

                        safe_text = json.dumps(full_response)

                        source_text = f"📚 <b>File:</b> {', '.join(sources)}" if sources else ""

                        components.html(
                            f"""
                            <style>
                            body {{
                                margin: 0;
                                padding: 0;
                                background: transparent;
                            }}

                            .bottom-bar {{
                                display:flex;
                                justify-content:space-between;
                                align-items:center;
                                font-size:14px;
                                color:#555;
                                margin-top:6px;
                            }}

                            .copy-btn {{
                                background:none;
                                border:none;
                                font-size:18px;
                                cursor:pointer;
                            }}
                            </style>

                            <div class="bottom-bar">

                                <div>{source_text}</div>

                                <button id="copyBtn" class="copy-btn">📋</button>

                            </div>

                            <script>
                            const textToCopy = {safe_text};
                            const btn = document.getElementById("copyBtn");

                            btn.onclick = function() {{
                                navigator.clipboard.writeText(textToCopy).then(() => {{
                                    btn.innerHTML = "✔️";

                                    setTimeout(() => {{
                                        btn.innerHTML = "📋";
                                    }}, 3000);
                                }});
                            }};
                            </script>
                            """,
                            height=40,
                        )

                messages.append(("assistant", full_response, sources))

                save_session()

    except Exception as e:
        st.error(f"Error generating answer: {e}")