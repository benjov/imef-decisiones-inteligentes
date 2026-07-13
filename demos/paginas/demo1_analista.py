"""Demo 1 — Analista financiero con IA.

Flujo: cargar datos → resumen rápido → "Analizar con IA" (streaming) →
gráficas que la IA decide → chat de seguimiento → descargar análisis.
"""

import json

import pandas as pd
import streamlit as st

from shared import estilos, respaldo, texto
from shared.cliente import obtener_cliente
from shared.config import DIR_DATA, MODELO
from shared.graficas import ESQUEMA_GRAFICAS, renderizar

estilos.aplicar()
modo_respaldo = respaldo.toggle_respaldo()

st.title("📊 Demo 1 · Analista financiero con IA")
st.caption("La IA lee datos crudos, decide qué es relevante, lo explica y lo grafica — en segundos.")

PROMPT_SISTEMA = """Eres un analista financiero senior de una empresa mediana mexicana.
Recibirás datos financieros u operativos crudos en CSV. Tu trabajo:

1. **Resumen de situación** (3-4 frases, lenguaje de dirección, no técnico).
2. **Anomalías y riesgos**: detecta y explica cualquier dato inusual, error de
   captura, tendencia preocupante o inconsistencia de calidad de datos. Sé específico
   (mes, monto, magnitud).
3. **Tres recomendaciones para el CFO**, accionables y priorizadas.

Responde en español, conciso, con encabezados Markdown (##) y cifras formateadas
(ej. $8.5 M). No inventes datos que no estén en la tabla."""


# ---------------------------------------------------------------- datasets --
DATASETS = {
    "Estado de resultados 2025 (12 meses)": "estado_resultados_2025.csv",
    "Ventas del semestre (datos sucios)": "ventas_sucias.csv",
}

eleccion = st.radio("Elige los datos a analizar:", [*DATASETS, "Subir mi propio archivo (CSV/XLSX)"],
                    horizontal=True)

df = None
if eleccion in DATASETS:
    df = pd.read_csv(DIR_DATA / DATASETS[eleccion])
else:
    archivo = st.file_uploader("Sube un CSV o Excel", type=["csv", "xlsx"])
    if archivo is not None:
        df = pd.read_csv(archivo) if archivo.name.endswith(".csv") else pd.read_excel(archivo)

if df is None:
    st.stop()

# reiniciar el análisis si cambia el dataset
if st.session_state.get("d1_dataset") != eleccion:
    for k in ("d1_analisis", "d1_graficas", "d1_chat", "d1_respaldo_idx"):
        st.session_state.pop(k, None)
    st.session_state["d1_dataset"] = eleccion

st.subheader("Los datos, tal como llegan")
st.dataframe(df, height=260, width="stretch")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Filas", f"{len(df):,}")
c2.metric("Columnas", len(df.columns))
c3.metric("Celdas vacías", f"{int(df.isna().sum().sum()) + int((df.astype(str) == '').sum().sum()):,}")
c4.metric("Filas duplicadas", f"{int(df.duplicated().sum()):,}")

csv_datos = df.to_csv(index=False)
if len(csv_datos) > 60_000:  # acotar datasets subidos muy grandes
    csv_datos = df.head(400).to_csv(index=False) + "\n... (truncado para la demo)"

st.markdown("---")


# ------------------------------------------------------------- análisis IA --
def analizar_real():
    cliente = obtener_cliente()
    with cliente.messages.stream(
        model=MODELO,
        max_tokens=2000,
        system=PROMPT_SISTEMA,
        messages=[{"role": "user", "content": f"Analiza estos datos:\n\n```csv\n{csv_datos}\n```"}],
    ) as stream:
        analisis = texto.stream_md(stream.text_stream)
    st.session_state["d1_analisis"] = analisis

    with st.spinner("La IA está decidiendo qué graficar…"):
        r = cliente.messages.create(
            model=MODELO,
            max_tokens=2500,
            system=("Eres un analista de datos. A partir de los datos y el análisis, decide "
                    "cuáles son las 2 o 3 gráficas que mejor cuentan la historia (tendencias, "
                    "anomalías). Usa cifras EXACTAS de los datos; marca en `resaltar_x` las "
                    "categorías anómalas. Etiquetas en español."),
            messages=[{"role": "user", "content":
                       f"Datos:\n```csv\n{csv_datos}\n```\n\nAnálisis previo:\n{analisis}"}],
            output_config={"format": {"type": "json_schema", "schema": ESQUEMA_GRAFICAS}},
        )
        bloque = next(b.text for b in r.content if b.type == "text")
        st.session_state["d1_graficas"] = json.loads(bloque)


def analizar_respaldo():
    datos = respaldo.cargar("demo1")
    analisis = texto.stream_md(respaldo.stream_falso(datos["analisis"]))
    st.session_state["d1_analisis"] = analisis
    st.session_state["d1_graficas"] = datos["graficas"]


if st.button("🔍 Analizar con IA", type="primary", disabled="d1_analisis" in st.session_state):
    if modo_respaldo:
        analizar_respaldo()
    else:
        analizar_real()
    st.rerun()

if "d1_analisis" in st.session_state:
    texto.markdown(st.session_state["d1_analisis"])
    st.download_button("⬇️ Descargar análisis (Markdown)",
                       st.session_state["d1_analisis"],
                       file_name="analisis_ia.md", mime="text/markdown")

if "d1_graficas" in st.session_state:
    st.subheader("Lo que la IA decidió graficar")
    renderizar(st.session_state["d1_graficas"])


# ------------------------------------------------------------ chat seguimiento --
if "d1_analisis" in st.session_state:
    st.markdown("---")
    st.subheader("Interroga a los datos")
    st.session_state.setdefault("d1_chat", [])

    for msg in st.session_state["d1_chat"]:
        with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🤖"):
            texto.markdown(msg["content"])

    pregunta = st.chat_input("Ej. ¿Por qué cayó el margen en agosto?")
    if pregunta:
        st.session_state["d1_chat"].append({"role": "user", "content": pregunta})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(pregunta)
        with st.chat_message("assistant", avatar="🤖"):
            if modo_respaldo:
                datos = respaldo.cargar("demo1")
                idx = st.session_state.get("d1_respaldo_idx", 0)
                respuestas = datos["chat"]
                resp_txt = respuestas[min(idx, len(respuestas) - 1)]["respuesta"]
                st.session_state["d1_respaldo_idx"] = idx + 1
                salida = texto.stream_md(respaldo.stream_falso(resp_txt))
            else:
                cliente = obtener_cliente()
                contexto = (f"Datos:\n```csv\n{csv_datos}\n```\n\n"
                            f"Tu análisis previo:\n{st.session_state['d1_analisis']}")
                mensajes = [{"role": "user", "content": contexto}]
                mensajes += [{"role": m["role"], "content": m["content"]}
                             for m in st.session_state["d1_chat"]]
                with cliente.messages.stream(
                    model=MODELO, max_tokens=1200, system=PROMPT_SISTEMA, messages=mensajes,
                ) as stream:
                    salida = texto.stream_md(stream.text_stream)
        st.session_state["d1_chat"].append({"role": "assistant", "content": salida})
