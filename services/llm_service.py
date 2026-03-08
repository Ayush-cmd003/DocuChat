import streamlit as st
from langchain_groq import ChatGroq
from config.settings import MODEL_NAME

@st.cache_resource(show_spinner=False)
def create_llm(api_key):

    return ChatGroq(
        model=MODEL_NAME,
        temperature=0.2,
        groq_api_key=api_key,
        reasoning_format="hidden",
        max_tokens=2000
    )