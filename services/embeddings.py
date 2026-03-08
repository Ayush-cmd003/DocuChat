import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from config.settings import EMBEDDING_MODEL


@st.cache_resource(show_spinner=False)
def load_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)