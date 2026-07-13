"""Demo 2 — Agente de punta a punta: correo → análisis → reporte → respuesta.

La audiencia VE el pipeline: el agente interpreta la solicitud, decide qué
herramientas usar (tool use real), redacta un reporte ejecutivo y deja listo
el correo de respuesta.
"""

import json

import streamlit as st

from shared import estilos, respaldo, texto
from shared.cliente import obtener_cliente
from shared.config import DIR_DATA, MODELO

estilos.aplicar()
modo_respaldo = respaldo.toggle_respaldo()

st.title("🤖 Demo 2 · Agente de punta a punta")
st.caption("De un correo del viernes a las 6 pm… a un reporte de comité. El agente decide cada paso.")

CORREOS = json.loads((DIR_DATA / "correos.json").read_text(encoding="utf-8"))

# ------------------------------------------------------- herramientas (tools) --
HERRAMIENTAS = [
    {
        "name": "consultar_ventas",
        "description": ("Consulta las ventas de un trimestre del año en curso, "
                        "desglosadas por línea de negocio. Úsala cuando necesites "
                        "cifras de ingresos o ventas."),
        "input_schema": {
            "type": "object",
            "properties": {"trimestre": {"type": "string", "enum": ["Q1", "Q2"],
                                          "description": "Trimestre a consultar"}},
            "required": ["trimestre"],
        },
    },
    {
        "name": "consultar_gastos",
        "description": ("Consulta los gastos de un trimestre del año en curso, "
                        "desglosados por categoría. Úsala cuando necesites cifras de costos o gastos."),
        "input_schema": {
            "type": "object",
            "properties": {"trimestre": {"type": "string", "enum": ["Q1", "Q2"],
                                          "description": "Trimestre a consultar"}},
            "required": ["trimestre"],
        },
    },
]


def ejecutar_herramienta(nombre: str, args: dict) -> str:
    archivo = "ventas_trimestrales.json" if nombre == "consultar_ventas" else "gastos_trimestrales.json"
    datos = json.loads((DIR_DATA / archivo).read_text(encoding="utf-8"))
    q = args.get("trimestre", "Q2")
    return json.dumps(datos.get(q, {"error": f"No hay datos para {q}"}), ensure_ascii=False)


# --------------------------------------------------------------- bandeja UI --
st.subheader("📥 Bandeja de entrada")
for c in CORREOS:
    st.markdown(
        f"""<div class="correo"><span class="fecha">{c['fecha']}</span>
        <div class="de">{c['de']}</div>
        <div class="asunto">{c['asunto']}</div></div>""",
        unsafe_allow_html=True,
    )

opciones = {f"{c['asunto']} — {c['de'].split('<')[0].strip()}": c for c in CORREOS}
sel = st.selectbox("Correo a atender:", list(opciones))
correo = opciones[sel]
with st.expander("Ver el correo completo", expanded=correo["id"] == 1):
    st.text(correo["cuerpo"])

tono = st.radio("Destinatario del reporte:", ["Comité (formal)", "Directora (directo)"],
                horizontal=True)


# ------------------------------------------------------------- pipeline real --
def pipeline_real():
    cliente = obtener_cliente()
    resultado = {"herramientas": []}

    with st.status("**Paso 1 — Interpretar la solicitud**", expanded=True) as status:
        r = cliente.messages.create(
            model=MODELO, max_tokens=500,
            system=("Eres un asistente ejecutivo. Lee el correo y explica en 3-4 líneas: "
                    "qué te están pidiendo, para cuándo, para quién es el entregable y qué "
                    "información vas a necesitar. Español, primera persona."),
            messages=[{"role": "user", "content": correo["cuerpo"]}],
        )
        interpretacion = next(b.text for b in r.content if b.type == "text")
        texto.markdown(interpretacion)
        resultado["interpretacion"] = interpretacion
        status.update(label="✅ Paso 1 — Solicitud interpretada", state="complete")

    with st.status("**Paso 2 — Consultar datos** (el agente decide qué herramienta usar)",
                   expanded=True) as status:
        mensajes = [{"role": "user", "content":
                     f"Correo recibido:\n{correo['cuerpo']}\n\n"
                     f"El reporte va dirigido a: {tono}. Elabora el reporte solicitado."}]
        sistema = ("Eres un analista financiero senior con acceso a herramientas de datos. "
                   "Consulta TODO lo que necesites (incluye el trimestre anterior si sirve para "
                   "comparar). Después redacta un reporte ejecutivo de UNA página en Markdown "
                   "con: título, resumen, cifras clave (ventas, gastos, utilidad, variaciones), "
                   "riesgos detectados y 3 recomendaciones. Español, cifras en formato $X.X M.")
        reporte = None
        while True:
            r = cliente.messages.create(
                model=MODELO, max_tokens=2500, system=sistema,
                tools=HERRAMIENTAS, messages=mensajes,
            )
            mensajes.append({"role": "assistant", "content": r.content})
            if r.stop_reason != "tool_use":
                reporte = next((b.text for b in r.content if b.type == "text"), "")
                break
            resultados_tools = []
            for bloque in r.content:
                if bloque.type == "tool_use":
                    st.markdown(f"🛠️ El agente decidió llamar **`{bloque.name}`** con "
                                f"argumentos `{json.dumps(bloque.input, ensure_ascii=False)}`")
                    salida = ejecutar_herramienta(bloque.name, bloque.input)
                    with st.expander(f"Resultado de `{bloque.name}({bloque.input.get('trimestre','')})`"):
                        st.code(salida, language="json")
                    resultado["herramientas"].append(
                        {"nombre": bloque.name, "args": bloque.input, "resultado": salida})
                    resultados_tools.append({"type": "tool_result",
                                             "tool_use_id": bloque.id, "content": salida})
            mensajes.append({"role": "user", "content": resultados_tools})
        status.update(label=f"✅ Paso 2 — {len(resultado['herramientas'])} consultas de datos ejecutadas",
                      state="complete")

    with st.status("**Paso 3 — Analizar y redactar el reporte**", expanded=True) as status:
        texto.markdown(reporte)
        resultado["reporte"] = reporte
        status.update(label="✅ Paso 3 — Reporte ejecutivo listo", state="complete")

    with st.status("**Paso 4 — Redactar la respuesta**", expanded=True) as status:
        r = cliente.messages.create(
            model=MODELO, max_tokens=600,
            system=("Redacta el correo de respuesta (breve, profesional, español) confirmando "
                    "que el reporte está listo y resumiendo en 3 viñetas los hallazgos clave. "
                    "Firma como 'Equipo de Análisis'. Solo el correo, sin comentarios."),
            messages=[{"role": "user", "content":
                       f"Correo original:\n{correo['cuerpo']}\n\nReporte elaborado:\n{reporte}"}],
        )
        correo_resp = next(b.text for b in r.content if b.type == "text")
        st.text(correo_resp)
        resultado["correo_respuesta"] = correo_resp
        status.update(label="✅ Paso 4 — Correo de respuesta listo (NO se envía solo)", state="complete")

    st.session_state["d2_resultado"] = resultado
    st.session_state["d2_recien"] = True


# --------------------------------------------------------- pipeline respaldo --
def pipeline_respaldo():
    datos = respaldo.cargar("demo2")
    resultado = dict(datos)

    with st.status("**Paso 1 — Interpretar la solicitud**", expanded=True) as status:
        texto.stream_md(respaldo.stream_falso(datos["interpretacion"]))
        status.update(label="✅ Paso 1 — Solicitud interpretada", state="complete")

    with st.status("**Paso 2 — Consultar datos** (el agente decide qué herramienta usar)",
                   expanded=True) as status:
        for h in datos["herramientas"]:
            st.markdown(f"🛠️ El agente decidió llamar **`{h['nombre']}`** con "
                        f"argumentos `{json.dumps(h['args'], ensure_ascii=False)}`")
            with st.expander(f"Resultado de `{h['nombre']}({h['args'].get('trimestre','')})`"):
                st.code(h["resultado"], language="json")
            import time as _t; _t.sleep(0.7)
        status.update(label=f"✅ Paso 2 — {len(datos['herramientas'])} consultas de datos ejecutadas",
                      state="complete")

    with st.status("**Paso 3 — Analizar y redactar el reporte**", expanded=True) as status:
        texto.stream_md(respaldo.stream_falso(datos["reporte"], pausa=0.008))
        status.update(label="✅ Paso 3 — Reporte ejecutivo listo", state="complete")

    with st.status("**Paso 4 — Redactar la respuesta**", expanded=True) as status:
        st.write_stream(respaldo.stream_falso(datos["correo_respuesta"]))
        status.update(label="✅ Paso 4 — Correo de respuesta listo (NO se envía solo)", state="complete")

    st.session_state["d2_resultado"] = resultado
    st.session_state["d2_recien"] = True


st.markdown("---")
if st.button("▶️ Ejecutar agente", type="primary"):
    st.session_state.pop("d2_resultado", None)
    if modo_respaldo:
        pipeline_respaldo()
    else:
        pipeline_real()

if "d2_resultado" in st.session_state:
    res = st.session_state["d2_resultado"]
    st.markdown("---")

    # Si la corrida NO acaba de suceder en este ciclo (p. ej. la app se
    # re-ejecutó al descargar), volver a mostrar el resultado completo.
    if not st.session_state.pop("d2_recien", False):
        with st.expander("Paso 1 — Interpretación de la solicitud"):
            texto.markdown(res.get("interpretacion", ""))
        with st.expander(f"Paso 2 — Consultas del agente ({len(res.get('herramientas', []))})"):
            for h in res.get("herramientas", []):
                st.markdown(f"🛠️ `{h['nombre']}` · argumentos "
                            f"`{json.dumps(h['args'], ensure_ascii=False)}`")
        st.subheader("📄 Reporte ejecutivo")
        texto.markdown(res.get("reporte", ""))
        st.subheader("✉️ Correo de respuesta (borrador)")
        st.text(res.get("correo_respuesta", ""))

    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Descargar reporte (.md)", res.get("reporte", ""),
                       file_name="reporte_ejecutivo.md", mime="text/markdown")
    c2.download_button("⬇️ Descargar correo de respuesta (.txt)", res.get("correo_respuesta", ""),
                       file_name="respuesta.txt", mime="text/plain")
    st.info("**El patrón correcto hoy:** el agente hace el 80% del trabajo; "
            "el humano revisa y decide. Este correo no se envía sin leerse.")
