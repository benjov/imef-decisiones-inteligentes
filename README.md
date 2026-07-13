# Decisiones Inteligentes: IA y el Futuro de las Empresas

Sitio y demos en vivo de la conferencia para **IMEF Morelos** (Cuernavaca, 16 de julio de 2026)
— Benjamín Oliva Vázquez, Analítica Boutique SC.

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

## Despliegue paso a paso

### 1. GitHub (repo público)

```bash
git remote add origin git@github.com:benjov/imef-decisiones-inteligentes.git
git push -u origin main
```

En GitHub: **Settings → Pages → Source: Deploy from a branch → `main` / `/docs`**.
La landing queda en `https://benjov.github.io/imef-decisiones-inteligentes/`.

### 2. Streamlit Community Cloud (demos 1 y 2)

1. Entra a [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub.
2. **New app** → repo `benjov/imef-decisiones-inteligentes` → branch `main` →
   main file `demos/app.py`.
3. En **Advanced settings → Secrets** pega:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
   (La key NUNCA va al repo: el repo es público.)
4. Deploy. La URL resultante (ej. `https://imef-demos.streamlit.app`) sirve la Demo 1;
   la Demo 2 queda en `<URL>/demo2_agente`.

### 3. Conectar la landing

Edita el bloque `const URLS = {...}` al tope de `docs/index.html` con las URLs reales
de Streamlit. El link de Colab ya apunta al notebook del repo. Commit + push.

### 4. QR del evento

El QR de las láminas L25/L26 debe apuntar a la landing (o directo a la sección
`.../#eventos`, que tiene el botón de contacto por correo).

## Correr todo en local (Plan C)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r demos/requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # y pon tu key
streamlit run demos/app.py
```

Las apps funcionan idéntico en local. Sin key (o sin internet), activa el
**Modo respaldo** en el panel lateral: reproduce corridas pre-grabadas simulando
el streaming — se ve igual que en vivo.

## Modo respaldo: cómo regrabarlo

Los respaldos viven en `demos/data/respaldos/demo{1,2}.json`. Para regrabarlos con
corridas reales (hazlo si cambias datasets o prompts):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python demos/record_run.py
```

> Los prompts de `record_run.py` son copia de los de `demos/paginas/*.py`;
> si cambias unos, actualiza los otros antes de regrabar.

Para regenerar los datasets (determinista, semilla fija):

```bash
python demos/data/generar_datos.py
```

Después de regenerar datos hay que regrabar respaldos y re-ejecutar el notebook
de respaldo:

```bash
cd notebooks && jupyter nbconvert --to notebook --execute --inplace demo3_codigo_asistido_RESPALDO.ipynb
```

## Datos sintéticos: qué tienen sembrado

| Dataset | Hallazgos que la IA debe "descubrir" |
|---|---|
| `estado_resultados_2025.csv` | Agosto: gasto operativo inusual (+$1.5 M, mes con pérdida) · Noviembre: error de captura (ingresos ×10) · margen bruto deteriorándose desde junio |
| `ventas_sucias.csv` | Formatos de fecha y monto inconsistentes, vacíos, duplicados, clientes con mayúsculas/minúsculas mezcladas |
| `ventas/gastos_trimestrales.json` (Demo 2) | Q2: Producto B cae ~10%, logística +22%, Servicios crece |
| `ventas_sucursales.csv` (Demo 3) | Cuernavaca Centro en declive (−36%) · Kit Industrial producto estrella (77% de la utilidad) · pico estacional en diciembre |

## Checklist pre-evento

**24 horas antes**
- [ ] Abrir las apps de Streamlit (Community Cloud duerme apps sin tráfico; el primer arranque tarda ~1 min).

**1 hora antes**
- [ ] Correr las demos 1 y 2 en **modo real** de punta a punta.
- [ ] Abrir la demo 3 en Colab desde el badge, con sesión de Google iniciada, y verificar que el asistente de IA de Colab está activo en esa cuenta.
- [ ] Probar el **modo respaldo** con el WiFi apagado (demos 1 y 2) y que `demo3_codigo_asistido_RESPALDO.ipynb` abre con outputs visibles.
- [ ] Tener la versión local lista (`streamlit run demos/app.py`) como plan C.
- [ ] Verificar saldo/límites de la API key en console.anthropic.com.

## Notas técnicas

- Modelo: `claude-sonnet-4-6` (constante en `demos/shared/config.py` y `demos/record_run.py`).
- Las gráficas de la Demo 1 las decide la IA: devuelve un JSON validado por esquema
  (structured outputs) que `shared/graficas.py` convierte en figuras Plotly.
- La Demo 2 usa **tool use real**: el modelo decide llamar `consultar_ventas` /
  `consultar_gastos` y la app muestra cada llamada con sus argumentos.
- Paleta de gráficas validada para contraste y daltonismo: azul `#2563EB`,
  ámbar `#B45309`, verde azulado `#0D9488`; rojo `#B91C1C` reservado para anomalías.
