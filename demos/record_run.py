"""Regraba los respaldos de las demos 1 y 2 con corridas reales de la API.

Uso (desde la raíz del repo, con ANTHROPIC_API_KEY en el entorno o en .env):

    python demos/record_run.py

Sobrescribe demos/data/respaldos/demo1.json y demo2.json. Correlo cada vez que
cambies los datasets o los prompts de las apps.

NOTA: los prompts de este script están copiados de demos/paginas/*.py — si
cambias un prompt allá, cámbialo también acá antes de regrabar.
"""

import json
import os
import sys
from pathlib import Path

import anthropic

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from shared.graficas import ESQUEMA_GRAFICAS  # noqa: E402

DATA = RAIZ / "data"
RESPALDOS = DATA / "respaldos"
MODELO = "claude-sonnet-4-6"

# cargar .env de la carpeta padre si existe (solo para uso local)
for env_path in [RAIZ.parent / ".env", RAIZ.parent.parent / ".env"]:
    if env_path.exists():
        for linea in env_path.read_text().splitlines():
            if linea.strip().startswith("ANTHROPIC_API_KEY") and "=" in linea:
                os.environ.setdefault("ANTHROPIC_API_KEY", linea.split("=", 1)[1].strip())

cliente = anthropic.Anthropic()

PROMPT_ANALISTA = """Eres un analista financiero senior de una empresa mediana mexicana.
Recibirás datos financieros u operativos crudos en CSV. Tu trabajo:

1. **Resumen de situación** (3-4 frases, lenguaje de dirección, no técnico).
2. **Anomalías y riesgos**: detecta y explica cualquier dato inusual, error de
   captura, tendencia preocupante o inconsistencia de calidad de datos. Sé específico
   (mes, monto, magnitud).
3. **Tres recomendaciones para el CFO**, accionables y priorizadas.

Responde en español, conciso, con encabezados Markdown (##) y cifras formateadas
(ej. $8.5 M). No inventes datos que no estén en la tabla."""


def grabar_demo1():
    print("Grabando demo 1…")
    csv_datos = (DATA / "estado_resultados_2025.csv").read_text()

    r = cliente.messages.create(
        model=MODELO, max_tokens=2000, system=PROMPT_ANALISTA,
        messages=[{"role": "user", "content": f"Analiza estos datos:\n\n```csv\n{csv_datos}\n```"}],
    )
    analisis = next(b.text for b in r.content if b.type == "text")

    r = cliente.messages.create(
        model=MODELO, max_tokens=2500,
        system=("Eres un analista de datos. A partir de los datos y el análisis, decide "
                "cuáles son las 2 o 3 gráficas que mejor cuentan la historia (tendencias, "
                "anomalías). Usa cifras EXACTAS de los datos; marca en `resaltar_x` las "
                "categorías anómalas. Etiquetas en español."),
        messages=[{"role": "user", "content":
                   f"Datos:\n```csv\n{csv_datos}\n```\n\nAnálisis previo:\n{analisis}"}],
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA_GRAFICAS}},
    )
    graficas = json.loads(next(b.text for b in r.content if b.type == "text"))

    # preguntas de seguimiento típicas del guión (en este orden se reproducen)
    preguntas = [
        "¿Por qué cayó el margen en agosto?",
        "¿Qué pasa con los ingresos de noviembre? ¿Son reales?",
        "¿Qué le dirías al consejo en una frase?",
    ]
    chat = []
    contexto = f"Datos:\n```csv\n{csv_datos}\n```\n\nTu análisis previo:\n{analisis}"
    mensajes = [{"role": "user", "content": contexto}]
    for p in preguntas:
        mensajes.append({"role": "user", "content": p})
        r = cliente.messages.create(model=MODELO, max_tokens=1200,
                                    system=PROMPT_ANALISTA, messages=mensajes)
        resp = next(b.text for b in r.content if b.type == "text")
        mensajes.append({"role": "assistant", "content": resp})
        chat.append({"pregunta": p, "respuesta": resp})

    (RESPALDOS / "demo1.json").write_text(
        json.dumps({"analisis": analisis, "graficas": graficas, "chat": chat},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print("  ✓ demo1.json")


HERRAMIENTAS = [
    {"name": "consultar_ventas",
     "description": ("Consulta las ventas de un trimestre del año en curso, desglosadas por "
                     "línea de negocio. Úsala cuando necesites cifras de ingresos o ventas."),
     "input_schema": {"type": "object",
                      "properties": {"trimestre": {"type": "string", "enum": ["Q1", "Q2"]}},
                      "required": ["trimestre"]}},
    {"name": "consultar_gastos",
     "description": ("Consulta los gastos de un trimestre del año en curso, desglosados por "
                     "categoría. Úsala cuando necesites cifras de costos o gastos."),
     "input_schema": {"type": "object",
                      "properties": {"trimestre": {"type": "string", "enum": ["Q1", "Q2"]}},
                      "required": ["trimestre"]}},
]


def ejecutar_herramienta(nombre, args):
    archivo = "ventas_trimestrales.json" if nombre == "consultar_ventas" else "gastos_trimestrales.json"
    datos = json.loads((DATA / archivo).read_text(encoding="utf-8"))
    return json.dumps(datos.get(args.get("trimestre", "Q2"), {}), ensure_ascii=False)


def grabar_demo2():
    print("Grabando demo 2…")
    correo = json.loads((DATA / "correos.json").read_text(encoding="utf-8"))[0]

    r = cliente.messages.create(
        model=MODELO, max_tokens=500,
        system=("Eres un asistente ejecutivo. Lee el correo y explica en 3-4 líneas: "
                "qué te están pidiendo, para cuándo, para quién es el entregable y qué "
                "información vas a necesitar. Español, primera persona."),
        messages=[{"role": "user", "content": correo["cuerpo"]}],
    )
    interpretacion = next(b.text for b in r.content if b.type == "text")

    herramientas_usadas = []
    mensajes = [{"role": "user", "content":
                 f"Correo recibido:\n{correo['cuerpo']}\n\n"
                 f"El reporte va dirigido a: Comité (formal). Elabora el reporte solicitado."}]
    sistema = ("Eres un analista financiero senior con acceso a herramientas de datos. "
               "Consulta TODO lo que necesites (incluye el trimestre anterior si sirve para "
               "comparar). Después redacta un reporte ejecutivo de UNA página en Markdown "
               "con: título, resumen, cifras clave (ventas, gastos, utilidad, variaciones), "
               "riesgos detectados y 3 recomendaciones. Español, cifras en formato $X.X M.")
    while True:
        r = cliente.messages.create(model=MODELO, max_tokens=2500, system=sistema,
                                    tools=HERRAMIENTAS, messages=mensajes)
        mensajes.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use":
            reporte = next((b.text for b in r.content if b.type == "text"), "")
            break
        resultados = []
        for b in r.content:
            if b.type == "tool_use":
                salida = ejecutar_herramienta(b.name, b.input)
                herramientas_usadas.append({"nombre": b.name, "args": b.input, "resultado": salida})
                resultados.append({"type": "tool_result", "tool_use_id": b.id, "content": salida})
        mensajes.append({"role": "user", "content": resultados})

    r = cliente.messages.create(
        model=MODELO, max_tokens=600,
        system=("Redacta el correo de respuesta (breve, profesional, español) confirmando "
                "que el reporte está listo y resumiendo en 3 viñetas los hallazgos clave. "
                "Firma como 'Equipo de Análisis'. Solo el correo, sin comentarios."),
        messages=[{"role": "user", "content":
                   f"Correo original:\n{correo['cuerpo']}\n\nReporte elaborado:\n{reporte}"}],
    )
    correo_resp = next(b.text for b in r.content if b.type == "text")

    (RESPALDOS / "demo2.json").write_text(
        json.dumps({"interpretacion": interpretacion, "herramientas": herramientas_usadas,
                    "reporte": reporte, "correo_respuesta": correo_resp},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print("  ✓ demo2.json")


if __name__ == "__main__":
    RESPALDOS.mkdir(parents=True, exist_ok=True)
    grabar_demo1()
    grabar_demo2()
    print("Respaldos regrabados.")
