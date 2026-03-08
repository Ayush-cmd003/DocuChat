import streamlit as st


def load_css(file_path: str):
    """
    Load an external CSS file into the Streamlit app.
    """
    with open(file_path) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )