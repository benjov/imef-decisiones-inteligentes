"""Estilos: legible desde la última fila del auditorio, look limpio."""

import streamlit as st

CSS = """
<style>
/* Ocultar menú, footer y decoración de Streamlit para un look limpio */
#MainMenu, footer, header [data-testid="stDecoration"] {visibility: hidden;}

/* Tipografía grande y alto contraste para proyector */
html, body, [data-testid="stAppViewContainer"] * {
    font-size: 1.02rem;
}
h1 {font-size: 2.1rem !important; color: #1F2937;}
h2 {font-size: 1.6rem !important; color: #1F2937;}
h3 {font-size: 1.3rem !important;}
[data-testid="stMetricValue"] {font-size: 1.9rem;}

/* Botón de acción principal más visible */
.stButton > button[kind="primary"] {
    font-size: 1.15rem;
    padding: 0.6rem 1.4rem;
}

/* Tarjetas de correo (demo 2) */
.correo {
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    background: #FFFFFF;
}
.correo .de {font-weight: 600; color: #1F2937;}
.correo .asunto {color: #2563EB; font-weight: 600;}
.correo .fecha {color: #6B7280; font-size: 0.9rem; float: right;}
</style>
"""


def aplicar():
    st.markdown(CSS, unsafe_allow_html=True)
