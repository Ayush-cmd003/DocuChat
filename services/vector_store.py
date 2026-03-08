import os
import streamlit as st
import shutil
import hashlib

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import VECTOR_DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP

@st.cache_resource(show_spinner=False)
def load_vector_store(_embeddings):

    persist_dir = st.session_state.vector_path

    if not os.path.exists(persist_dir):
        return None

    try:
        return Chroma(
            persist_directory=persist_dir,
            embedding_function=_embeddings
        )

    except Exception:
        shutil.rmtree(VECTOR_DB_PATH, ignore_errors=True)
        return None


def add_documents(vector_store, embeddings, text, filename):

    docs = [Document(page_content=text.lower(), metadata={"source": filename})]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = splitter.split_documents(docs)

    # Generate unique IDs for each chunk
    ids = []
    unique_chunks = []

    for chunk in chunks:
        content = chunk.page_content
        chunk_id = hashlib.md5((filename + content).encode()).hexdigest()

        ids.append(chunk_id)
        unique_chunks.append(chunk)

    # If vector DB doesn't exist yet
    if vector_store is None:

        db = Chroma.from_documents(
            unique_chunks,
            embeddings,
            ids=ids,
            persist_directory=st.session_state.vector_path
        )

        db.persist()
        return db

    vector_store.add_documents(unique_chunks, ids=ids)
    vector_store.persist()
    return vector_store