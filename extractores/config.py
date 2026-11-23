"""Configuracion central de AbarrotesPOS (observatorio de ventas y precios para tiendas).

Todo lo que cambia entre equipos, clientes o entregas vive aqui, no regado en el codigo.
"""

import os
from pathlib import Path

VERSION = "0.2.0"

# --- Identificacion honesta del extractor (regla del proyecto) ---------------
# En GitHub se define como variable del repositorio TDL_CONTACTO.
CONTACTO = os.environ.get("TDL_CONTACTO", "github.com/salvadorafer11/abarrotespos")
USER_AGENT = (
    f"TDL-AbarrotesPOS/{VERSION} (proyecto academico TecNM campus Colima; contacto: {CONTACTO})"
)
ZONA_HORARIA = "America/Mexico_City"

# --- Rutas ---------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DIR_BRONCE = RAIZ / "data" / "bronce"
DIR_PLATA = RAIZ / "data" / "plata"
DIR_ORO = RAIZ / "data" / "oro"
DIR_CUARENTENA = RAIZ / "data" / "cuarentena"
DIR_CALIDAD = RAIZ / "calidad"
BITACORA = RAIZ / "calidad" / "bitacora-captura.csv"

# --- Zona y cliente piloto -------------------------------------------------------
# Tienda piloto: Abarrotes "El Amiguito" (col. General Manuel Alvarez, Villa de Alvarez).
# J3 (Julio): coordenadas reales tomadas de Google Maps (clic derecho -> copiar coordenadas).
# Mientras sean None se usa el centro de Villa de Alvarez y el tablero lo avisa.
# Son coordenadas de un NEGOCIO, no de una persona.
TIENDA_LAT = None
TIENDA_LON = None
TIENDA_PILOTO = {
    "nombre": "Abarrotes El Amiguito (piloto)",
    "lat": float(os.environ.get("TIENDA_LAT") or TIENDA_LAT or 19.2675),
    "lon": float(os.environ.get("TIENDA_LON") or TIENDA_LON or -103.7375),
    "coordenadas_confirmadas": TIENDA_LAT is not None or bool(os.environ.get("TIENDA_LAT")),
}
# Caja de Colima + Villa de Alvarez (sur, oeste, norte, este) para la fuente geoespacial.
BBOX_ZONA = (19.20, -103.78, 19.31, -103.67)
RADIO_COMPETENCIA_M = 500  # tiendas a menos de esto se cuentan como competencia directa

# --- Open-Meteo (clima diario; API sin llave) -----------------------------------
OPEN_METEO_ARCHIVO = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_VARIABLES = "temperature_2m_max,temperature_2m_min,precipitation_sum"
CLIMA_DESDE = "2025-01-01"

# --- OpenStreetMap / Overpass (fuente especializada geoespacial de E2) -------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_GIROS = ["convenience", "supermarket", "greengrocer", "butcher", "general", "kiosk"]

# --- INEGI DENUE (alternativa geoespacial con giro SCIAN; token gratuito) ----------
# SCIAN 461110 = comercio al por menor en tiendas de abarrotes, ultramarinos y misceláneas.
DENUE_BASE = "https://www.inegi.org.mx/app/api/denue/v1/consulta"
DENUE_SCIAN_ABARROTES = "461110"

# --- PROFECO "Quien es Quien en los Precios" (precios de mercado; datos abiertos) -------
QQP_CATALOGO = "https://datos.gob.mx/busca/dataset/quien-es-quien-en-los-precios"


def denue_token():
    token = os.environ.get("DENUE_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Falta DENUE_TOKEN (token gratuito de INEGI); va en GitHub Secrets")
    return token
