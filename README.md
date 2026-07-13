# Decisiones Inteligentes: IA y el Futuro de las Empresas

Sitio y demos en vivo de la conferencia para **IMEF Morelos** (Cuernavaca, 16 de julio de 2026)
— Benjamín Oliva Vázquez, Analítica Boutique SC.

Página del evento: https://benjov.github.io/imef-decisiones-inteligentes/

| Pieza | Tecnología | Dónde vive |
|---|---|---|
| Landing + recursos | HTML/CSS/JS vanilla | GitHub Pages (`/docs`) |
| Demo 1 · Analista financiero · Demo 2 · Agente | Streamlit (app multipágina) | Streamlit Community Cloud (`demos/app.py`) |
| Demo 3 · Código asistido | Jupyter/Colab | `notebooks/` (badge "Open in Colab") |

## Estructura

```
├── docs/                    → GitHub Pages (landing + recursos)
├── demos/
│   ├── app.py               → entrada de la app multipágina (Streamlit)
│   ├── paginas/             → demo1_analista.py, demo2_agente.py
│   ├── shared/              → cliente Anthropic, estilos, gráficas, modo respaldo
│   ├── data/                → datasets sintéticos + respaldos pre-grabados (JSON)
│   │   └── generar_datos.py → regenera TODOS los datasets (determinista)
│   ├── record_run.py        → regraba los respaldos con corridas reales de la API
│   └── requirements.txt
├── notebooks/
│   ├── demo3_codigo_asistido.ipynb           → notebook base (casi vacío, para Colab)
│   ├── demo3_codigo_asistido_RESPALDO.ipynb  → ya ejecutado, con gráficas visibles
│   └── data/ventas_sucursales.csv
└── .streamlit/config.toml   → tema visual
```

