"""Cliente Anthropic: resuelve la API key desde Streamlit secrets o el entorno."""

import os

import anthropic
import streamlit as st


@st.cache_resource
def obtener_cliente() -> anthropic.Anthropic:
    """La key vive en st.secrets (Streamlit Cloud) o en ANTHROPIC_API_KEY (local).

    Nunca en el repo: el repo es público por GitHub Pages.
    """
    api_key = None
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error(
            "No se encontró `ANTHROPIC_API_KEY`. Configúrala en los Secrets de "
            "Streamlit Cloud o como variable de entorno (ver README). "
            "Mientras tanto puedes usar el **Modo respaldo** del panel lateral."
        )
        st.stop()
    return anthropic.Anthropic(api_key=api_key)


def hay_api_key() -> bool:
    try:
        if st.secrets["ANTHROPIC_API_KEY"]:
            return True
    except (KeyError, FileNotFoundError):
        pass
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
