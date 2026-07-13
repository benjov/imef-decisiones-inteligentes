"""App multipágina de las demos — un solo despliegue en Streamlit Community Cloud.

Correr local:  streamlit run demos/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# asegurar que `shared` sea importable aunque Streamlit corra desde otra carpeta
sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="Decisiones Inteligentes · Demos IMEF",
    page_icon="💡",
    layout="wide",
)

paginas = st.navigation([
    st.Page("paginas/demo1_analista.py", title="Demo 1 · Analista financiero",
            icon="📊", default=True),
    st.Page("paginas/demo2_agente.py", title="Demo 2 · Agente de punta a punta",
            icon="🤖"),
])
paginas.run()
