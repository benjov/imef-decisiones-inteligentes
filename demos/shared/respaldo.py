"""Modo respaldo: reproduce corridas pre-grabadas simulando streaming.

Los archivos JSON viven en demos/data/respaldos/ y se regraban con
`python demos/record_run.py` (requiere API key y conexión).
"""

import json
import time
from typing import Iterator

import streamlit as st

from .config import DIR_RESPALDOS


def cargar(nombre: str) -> dict:
    ruta = DIR_RESPALDOS / f"{nombre}.json"
    if not ruta.exists():
        st.error(f"No existe el respaldo `{ruta.name}`. Regrábalo con `python demos/record_run.py`.")
        st.stop()
    return json.loads(ruta.read_text(encoding="utf-8"))


def stream_falso(texto: str, pausa: float = 0.012) -> Iterator[str]:
    """Emite el texto en pedazos pequeños para que se vea como streaming real."""
    palabras = texto.split(" ")
    for i in range(0, len(palabras), 3):
        yield " ".join(palabras[i:i + 3]) + " "
        time.sleep(pausa)


def toggle_respaldo() -> bool:
    """Toggle discreto en el sidebar. Devuelve True si el modo respaldo está activo."""
    with st.sidebar:
        st.markdown("---")
        activo = st.toggle(
            "Modo respaldo",
            value=st.session_state.get("modo_respaldo", False),
            help="Reproduce corridas pre-grabadas sin llamar a la API (no requiere internet).",
        )
        st.session_state["modo_respaldo"] = activo
    return activo
