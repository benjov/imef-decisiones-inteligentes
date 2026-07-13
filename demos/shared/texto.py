"""Utilidades de texto para render en Streamlit.

Streamlit interpreta `$...$` en Markdown como fórmula LaTeX, así que los montos
("$8.9 M ... $1.6 M") se deforman. Se escapa `$` SOLO al renderizar; el texto
guardado (y el de las descargas) queda intacto.
"""

from typing import Iterable, Iterator

import streamlit as st


def escapar(texto: str) -> str:
    """Escapa los signos de pesos para que Markdown no los tome como LaTeX."""
    return texto.replace("$", "\\$")


def markdown(texto: str) -> None:
    """st.markdown seguro para texto con montos en pesos."""
    st.markdown(escapar(texto))


def stream_md(chunks: Iterable[str]) -> str:
    """Renderiza un stream escapando `$` y devuelve el texto CRUDO acumulado."""
    crudo: list[str] = []

    def gen() -> Iterator[str]:
        for c in chunks:
            crudo.append(c)
            yield c.replace("$", "\\$")

    st.write_stream(gen())
    return "".join(crudo)
