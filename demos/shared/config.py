"""Configuración compartida de las demos."""

from pathlib import Path

# Modelo sugerido en la especificación de la charla; cambiar aquí si se desea otro.
MODELO = "claude-sonnet-4-6"

DIR_DEMOS = Path(__file__).resolve().parent.parent      # demos/
DIR_DATA = DIR_DEMOS / "data"
DIR_RESPALDOS = DIR_DATA / "respaldos"

# Paleta validada (contraste y daltonismo) para proyector, fondo claro.
COLOR_PRIMARIO = "#2563EB"   # azul — serie principal
COLOR_SECUNDARIO = "#B45309" # ámbar — serie de contraste
COLOR_TERCIARIO = "#0D9488"  # verde azulado
COLOR_NEGATIVO = "#B91C1C"   # rojo — reservado para anomalías / caídas
PALETA = [COLOR_PRIMARIO, COLOR_SECUNDARIO, COLOR_TERCIARIO, COLOR_NEGATIVO]

COLOR_TEXTO = "#1F2937"
COLOR_TEXTO_SUAVE = "#6B7280"
