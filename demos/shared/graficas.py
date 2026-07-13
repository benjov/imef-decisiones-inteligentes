"""Renderiza las gráficas que la IA decide mostrar (Demo 1).

La IA devuelve un JSON con especificaciones simples; aquí se convierten en
figuras Plotly con un estilo consistente (marcas delgadas, paleta validada,
rojo reservado para resaltar anomalías).
"""

import plotly.graph_objects as go
import streamlit as st

from .config import COLOR_NEGATIVO, PALETA

# Esquema que se le pide a la IA (structured outputs)
ESQUEMA_GRAFICAS = {
    "type": "object",
    "properties": {
        "graficas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["barras", "linea"]},
                    "titulo": {"type": "string"},
                    "eje_x": {"type": "array", "items": {"type": "string"}},
                    "series": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string"},
                                "valores": {"type": "array", "items": {"type": "number"}},
                            },
                            "required": ["nombre", "valores"],
                            "additionalProperties": False,
                        },
                    },
                    "resaltar_x": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Categorías del eje X a resaltar en rojo (anomalías).",
                    },
                    "razon": {
                        "type": "string",
                        "description": "Una frase: por qué esta gráfica cuenta la historia.",
                    },
                },
                "required": ["tipo", "titulo", "eje_x", "series", "resaltar_x", "razon"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["graficas"],
    "additionalProperties": False,
}

_LAYOUT_BASE = dict(
    template="plotly_white",
    font=dict(size=16, color="#1F2937"),
    margin=dict(l=10, r=10, t=48, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    yaxis=dict(gridcolor="#F3F4F6", zerolinecolor="#E5E7EB", tickformat="~s"),
    xaxis=dict(showgrid=False),
    hovermode="x unified",
)


def renderizar(spec: dict) -> None:
    """Dibuja todas las gráficas de la especificación devuelta por la IA."""
    for g in spec.get("graficas", []):
        fig = go.Figure()
        resaltar = set(g.get("resaltar_x") or [])
        una_serie = len(g["series"]) == 1
        for i, serie in enumerate(g["series"]):
            color = PALETA[i % len(PALETA)]
            if g["tipo"] == "barras":
                colores = [COLOR_NEGATIVO if x in resaltar else color for x in g["eje_x"]]
                fig.add_bar(
                    x=g["eje_x"], y=serie["valores"],
                    name=serie["nombre"], marker_color=colores,
                    marker_line_width=0, width=0.62,
                )
            else:
                fig.add_scatter(
                    x=g["eje_x"], y=serie["valores"], name=serie["nombre"],
                    mode="lines+markers",
                    line=dict(color=color, width=2),
                    marker=dict(size=8, color=color),
                )
        if g["tipo"] == "linea" and resaltar:
            # puntos rojos sobre las categorías anómalas de la primera serie
            s0 = g["series"][0]
            xs = [x for x in g["eje_x"] if x in resaltar]
            ys = [s0["valores"][g["eje_x"].index(x)] for x in xs]
            fig.add_scatter(
                x=xs, y=ys, mode="markers", name="Anomalía",
                marker=dict(size=13, color=COLOR_NEGATIVO, symbol="circle-open",
                            line=dict(width=3, color=COLOR_NEGATIVO)),
            )
        fig.update_layout(
            title=dict(text=g["titulo"], font=dict(size=19)),
            showlegend=not una_serie or bool(resaltar and g["tipo"] == "linea"),
            **_LAYOUT_BASE,
        )
        st.plotly_chart(fig, width="stretch")
        if g.get("razon"):
            st.caption(f"🤖 Por qué la IA eligió esta gráfica: {g['razon']}")
