"""Genera todos los datasets sintéticos de las demos.

Correr desde la raíz del repo:  python demos/data/generar_datos.py
Es determinista (semilla fija): regenerar produce exactamente los mismos datos,
así los respaldos pre-grabados siguen siendo coherentes con los CSV.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parent          # demos/data/
NOTEBOOKS = RAIZ.parent.parent / "notebooks" / "data"
rng = np.random.default_rng(42)

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


# ---------------------------------------------------------------------------
# Demo 1a — Estado de resultados mensual (12 meses, año 2025) con anomalías:
#   * Agosto: gasto operativo inusual (proyecto fallido de TI)
#   * Margen bruto deteriorándose desde junio (alza de costo de insumos)
#   * Noviembre: error de captura (ingresos con un dígito de más)
# ---------------------------------------------------------------------------
def estado_resultados():
    base_ingresos = 8_500_000
    filas = []
    for i, mes in enumerate(MESES):
        estacionalidad = 1.0 + 0.05 * np.sin(i / 11 * 2 * np.pi) + (0.18 if i == 11 else 0)
        ingresos = base_ingresos * estacionalidad * (1 + 0.006 * i) * rng.normal(1, 0.015)
        # el costo sube gradualmente a partir de junio (margen se deteriora)
        pct_costo = 0.58 + (0.025 * max(0, i - 5) / 6)
        costo_ventas = ingresos * pct_costo * rng.normal(1, 0.01)
        gasto_admin = 950_000 * rng.normal(1, 0.03)
        gasto_ventas = ingresos * 0.085 * rng.normal(1, 0.04)
        gasto_operativo = 720_000 * rng.normal(1, 0.03)
        if i == 7:  # Agosto: anomalía de gasto
            gasto_operativo += 1_450_000
        ingresos_final = ingresos
        if i == 10:  # Noviembre: error de captura (un cero de más)
            ingresos_final = ingresos * 10
        filas.append({
            "Mes": mes,
            "Ingresos": round(ingresos_final, 0),
            "Costo_de_Ventas": round(costo_ventas, 0),
            "Gasto_Administrativo": round(gasto_admin, 0),
            "Gasto_de_Ventas": round(gasto_ventas, 0),
            "Gasto_Operativo": round(gasto_operativo, 0),
        })
    df = pd.DataFrame(filas)
    df["Utilidad_Bruta"] = df["Ingresos"] - df["Costo_de_Ventas"]
    df["Utilidad_Operativa"] = (df["Utilidad_Bruta"] - df["Gasto_Administrativo"]
                                - df["Gasto_de_Ventas"] - df["Gasto_Operativo"])
    df.to_csv(RAIZ / "estado_resultados_2025.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# Demo 1b — Ventas "sucias": formatos inconsistentes, vacíos, duplicados
# ---------------------------------------------------------------------------
def ventas_sucias():
    n = 220
    clientes = ["Comercial del Valle", "GRUPO ATLAS", "grupo atlas", "Distribuidora Mx",
                "Ferretera López", "FERRETERA LOPEZ SA", "Abarrotes Central",
                "Constructora Sur", None, "Papelera Nacional"]
    productos = ["Tornillería", "Adhesivos", "Herramienta", "Pintura", "Eléctrico"]
    filas = []
    for _ in range(n):
        fecha_dt = pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 180)))
        formato = rng.choice(["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%y"])
        monto = float(rng.lognormal(9.2, 0.7))
        monto_txt = rng.choice([
            f"{monto:,.2f}", f"${monto:,.0f}", f"{monto:.2f}", ""
        ], p=[0.5, 0.25, 0.2, 0.05])
        filas.append({
            "fecha": fecha_dt.strftime(formato),
            "cliente": rng.choice(clientes),
            "producto": rng.choice(productos),
            "monto": monto_txt,
            "vendedor": rng.choice(["A. Ríos", "M. Peña", "J. Cortés", "a. rios", ""]),
        })
    df = pd.DataFrame(filas)
    # duplicados exactos sembrados
    df = pd.concat([df, df.sample(12, random_state=7)], ignore_index=True)
    df = df.sample(frac=1, random_state=7).reset_index(drop=True)
    df.to_csv(RAIZ / "ventas_sucias.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# Demo 2 — Datos trimestrales que consultan las herramientas del agente
# ---------------------------------------------------------------------------
def datos_agente():
    ventas = {}
    gastos = {}
    lineas = ["Producto A", "Producto B", "Servicios"]
    base = {"Producto A": 4_200_000, "Producto B": 2_900_000, "Servicios": 1_600_000}
    for q in ["Q1", "Q2"]:
        factor_q = 1.0 if q == "Q1" else 1.07
        ventas[q] = {
            "trimestre": q, "anio": 2026, "moneda": "MXN",
            "por_linea": [],
        }
        for ln in lineas:
            # Producto B cae en Q2 (pierde un cliente grande); lo demás crece
            f = 0.86 if (q == "Q2" and ln == "Producto B") else factor_q
            monto = round(base[ln] * 3 * f * float(rng.normal(1, 0.02)), 0)
            ventas[q]["por_linea"].append({"linea": ln, "ventas": monto})
        ventas[q]["total"] = round(sum(x["ventas"] for x in ventas[q]["por_linea"]), 0)
        gastos[q] = {
            "trimestre": q, "anio": 2026, "moneda": "MXN",
            "por_categoria": [
                {"categoria": "Nómina", "gasto": round(5_100_000 * factor_q, 0)},
                {"categoria": "Logística", "gasto": round(1_950_000 * (1.22 if q == "Q2" else 1.0), 0)},
                {"categoria": "Marketing", "gasto": round(880_000 * factor_q, 0)},
                {"categoria": "Tecnología", "gasto": round(640_000, 0)},
                {"categoria": "Otros", "gasto": round(510_000, 0)},
            ],
        }
        gastos[q]["total"] = round(sum(x["gasto"] for x in gastos[q]["por_categoria"]), 0)

    (RAIZ / "ventas_trimestrales.json").write_text(
        json.dumps(ventas, ensure_ascii=False, indent=2), encoding="utf-8")
    (RAIZ / "gastos_trimestrales.json").write_text(
        json.dumps(gastos, ensure_ascii=False, indent=2), encoding="utf-8")

    correos = [
        {
            "id": 1,
            "de": "Laura Mendoza <lmendoza@empresa.mx>",
            "asunto": "Resumen de desempeño Q2 para el comité",
            "fecha": "Viernes 17:58",
            "cuerpo": ("Buenas tardes,\n\nNecesito para mañana un resumen del desempeño de Q2 "
                       "con riesgos y recomendaciones para el comité. Una página máximo.\n\n"
                       "Gracias,\nLaura Mendoza\nDirectora General"),
        },
        {
            "id": 2,
            "de": "Recursos Humanos <rh@empresa.mx>",
            "asunto": "Recordatorio: encuesta de clima laboral",
            "fecha": "Viernes 16:40",
            "cuerpo": "Recuerda contestar la encuesta de clima laboral antes del lunes.",
        },
        {
            "id": 3,
            "de": "Proveedor Logístico <facturacion@translog.mx>",
            "asunto": "Factura F-20449 disponible",
            "fecha": "Viernes 15:12",
            "cuerpo": "Estimado cliente, su factura del periodo está disponible en el portal.",
        },
    ]
    (RAIZ / "correos.json").write_text(
        json.dumps(correos, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Demo 3 — Ventas por sucursal (Colab): 5 sucursales, 18 meses.
# Hallazgos sembrados: Cuernavaca Centro en declive, "Kit Industrial" producto
# estrella, estacionalidad clara en diciembre.
# ---------------------------------------------------------------------------
def ventas_sucursales():
    sucursales = ["Cuernavaca Centro", "Cuernavaca Norte", "Jiutepec",
                  "Temixco", "Cuautla"]
    productos = {
        "Kit Industrial": (5200, 3100),
        "Línea Hogar": (1450, 900),
        "Refacciones": (880, 520),
        "Consumibles": (320, 210),
    }
    base_suc = {"Cuernavaca Centro": 1.35, "Cuernavaca Norte": 1.1, "Jiutepec": 0.95,
                "Temixco": 0.7, "Cuautla": 0.85}
    fechas = pd.date_range("2024-07-01", periods=18, freq="MS")
    filas = []
    for t, fecha in enumerate(fechas):
        for suc in sucursales:
            nivel = base_suc[suc]
            if suc == "Cuernavaca Centro":      # declive sostenido
                nivel *= (1 - 0.028) ** t
            elif suc == "Jiutepec":             # crecimiento sano
                nivel *= (1 + 0.012) ** t
            if fecha.month == 12:               # estacionalidad navideña
                nivel *= 1.45
            for prod, (precio, costo) in productos.items():
                unidades = max(0, int(rng.normal(38, 6) * nivel *
                                      (1.6 if prod == "Kit Industrial" else 1.0)))
                filas.append({
                    "fecha": fecha.strftime("%Y-%m-%d"),
                    "sucursal": suc,
                    "producto": prod,
                    "unidades": unidades,
                    "precio_unitario": round(precio * float(rng.normal(1, 0.015)), 2),
                    "costo_unitario": round(costo * float(rng.normal(1, 0.01)), 2),
                })
    df = pd.DataFrame(filas)
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    df.to_csv(NOTEBOOKS / "ventas_sucursales.csv", index=False)
    return df


if __name__ == "__main__":
    estado_resultados()
    ventas_sucias()
    datos_agente()
    ventas_sucursales()
    print("Datasets generados en demos/data/ y notebooks/data/")
