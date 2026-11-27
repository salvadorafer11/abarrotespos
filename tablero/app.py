"""Tablero de AbarrotesPOS para el dueño de la tienda.  streamlit run tablero/app.py

Estilo de app de punto de venta: fondo azul muy claro, tarjetas blancas redondeadas con sombra
suave, una sola tipografía sans en negritas (Plus Jakarta Sans) y un solo color de acento
(azul). Arriba: barra con logo y pestañas de sección; saludo junto a una tarjeta azul con el
informe; 4 indicadores del mes en fila; promedios por día y productos que más dejaron. El
color en las gráficas se reserva para lo que significa algo (día fuerte y eventos en verde,
calor, fiado). Streamlit quita las etiquetas <script>, así que todo el diseño va en ESTILOS;
el tema base vive en .streamlit/config.toml.

Cada tarjeta tiene título de una línea, nota de una línea y gráfica de altura fija, para que
las tarjetas de una misma fila midan lo mismo.
"""

import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
ORO = RAIZ / "data" / "oro"
PLATA = RAIZ / "data" / "plata"
sys.path.insert(0, str(RAIZ))
from extractores.config import RADIO_COMPETENCIA_M, TIENDA_PILOTO  # noqa: E402
from tablero.buscador import buscar, documento, hubo_correccion  # noqa: E402
from tablero.productos import ficha, imagen, nombre  # noqa: E402

# --- PALETA: un solo azul de acento sobre blanco y gris pizarra -------------------------------
TINTA = "#0F172A"  # títulos y cifras
TEXTO = "#1E293B"
TEXTO_EJE = "#64748B"
REJILLA = "rgba(15, 23, 42, 0.06)"
AZUL = "#2563EB"  # acento: dato principal de las gráficas
AZUL_CLARO = "#A9C3F7"  # dato secundario
AZUL_MEDIO = "#7EA6F4"
AMBAR = "#F59E0B"  # mejor día y primer lugar
AMBAR_TEXTO = "#B45309"
VERDE = "#059669"  # competencia directa, cambios buenos
ROJO = "#E11D48"  # cambios malos
GRIS = "#94A3B8"  # resto de las tiendas
FUENTE = "'Plus Jakarta Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
# Degradados: escala de ganancia (azul claro a azul), día más fuerte y días con evento (verde),
# días normales (verde muy claro), demás días de la semana (azul muy claro) y fiado (rosa).
ESCALA_AZUL = ["#C7D8FB", AZUL]
VERDE_FUERTE = ("#047857", "#059669", "#10B981")
VERDE_SUAVE = ("#A7F3D0", "#D1FAE5")
AZUL_SUAVE = ("#DBE7FE", "#B9CFFB")
ROSA = ("#FECDD3", "#FB7185", "#E11D48")
# Escala de temperatura: azul claro (fresco) -> amarillo neutro -> naranja amarillo fuerte ->
# naranja rojo (lo más caluroso).
TRAMOS_CALOR = {"Menos de 29 °C": "#5DADEC", "29 a 31 °C": "#E9C94F",
                "31 a 33 °C": "#F59E0B", "Más de 33 °C": "#EA5A2C"}

ALTO_SERIE = 280  # gráfica de venta diaria (ancho completo)
ALTO_FILA = 320  # gráficas de las filas de tarjetas
ALTO_MAPA = 420

DIAS_LARGOS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DIAS = {"Monday": "Lun", "Tuesday": "Mar", "Wednesday": "Mié", "Thursday": "Jue",
        "Friday": "Vie", "Saturday": "Sáb", "Sunday": "Dom"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
EVENTOS = {"normal": "Día normal", "cabalgata": "Cabalgata",
           "fiestas_charrotaurinas": "Fiestas charrotaurinas", "navidad": "Navidad"}
# Vistas del tablero: el inicio (resumen) y una vista por tema, a la que se entra con su botón
# de acceso rápido o con su pestaña. clave -> (pestaña, icono, título, descripción).
VISTAS = {
    "inicio": ("Resumen", "barras", "Resumen del mes",
               "Indicadores, promedios por día y productos con más ganancia."),
    "informe": ("Informe", "informe", "Informe del mes",
                "Cómo vas contra el mes anterior, qué cambió y lo que hay que saber."),
    "venta": ("Venta", "serie", "Venta por día",
              "Cómo se movió la venta día a día y cuál fue el mejor día."),
    "productos": ("Productos", "productos", "Productos y días fuertes",
                  "Productos con más ganancia, días que más venden y efecto de los eventos."),
    "precios": ("Precios", "precios", "Precios del mercado",
                "Tus precios contra los de PROFECO y dónde conviene surtir."),
    "competencia": ("Competencia", "mapa", "Competencia en la zona",
                    "Tiendas alrededor de la tienda piloto y la más cercana."),
    "clima": ("Clima y crédito", "clima", "Clima y crédito",
              "Cómo cambia la venta con el calor y quién debe más fiado."),
}
# Iconos (Heroicons, MIT).
ICONOS = {
    "barras": "M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 "
              "20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-"
              ".621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 "
              "1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621"
              ".504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-"
              "1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z",
    "flecha": "M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3",
    "atras": "M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18",
    "venta": "M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 "
             "0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879"
             "-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 "
             "18 0Z",
    "ganancia": "M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94"
                "-2.281m5.94 2.28-2.28 5.941",
    "tickets": "M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5.25h5.25M7.5 15h3M3.375 5.25c-.621 0"
               "-1.125.504-1.125 1.125v3.026a2.999 2.999 0 0 1 0 5.198v3.026c0 .621.504 1.125 "
               "1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 0 1 0-5.198"
               "V6.375c0-.621-.504-1.125-1.125-1.125H3.375Z",
    "fiado": "M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    "chispa": "M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 "
              "4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813"
              "a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-"
              "2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a"
              "3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z",
    "descarga": "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 "
                "12 16.5m0 0L7.5 12m4.5 4.5V3",
    "informe": "M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 "
               "7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25M9 16.5v.75m3-3v3M15 12v5.25m-4.5-15"
               "H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621"
               " 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z",
    "imprimir": "M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0 1 10.56 0m"
                "-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0 .229 "
                "2.523a1.125 1.125 0 0 1-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m"
                "11.318 0h1.091A2.25 2.25 0 0 0 21 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a"
                "48.055 48.055 0 0 0-1.913-.247M6.34 18H5.25A2.25 2.25 0 0 1 3 15.75V9.456c0-1.081"
                ".768-2.015 1.837-2.175a48.041 48.041 0 0 1 1.913-.247m10.5 0a48.536 48.536 0 0 "
                "0-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125"
                " 1.125v3.659M18 10.5h.008v.008H18V10.5Zm-3 0h.008v.008H15V10.5Z",
    "precios": "M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 "
               "9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369"
               "-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3ZM6 6h.008v.008H6V6Z",
    "buscar": "m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 "
              "10.607Z",
    "sube": "m4.5 19.5 15-15m0 0H8.25m11.25 0v11.25",
    "baja": "m4.5 4.5 15 15m0 0V8.25m0 11.25H8.25",
    "tienda": "M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18"
              "m0 0h3.64m-1.39 0V9.349M3.75 21V9.349m0 0a3.004 3.004 0 0 0 3.75-.615A2.993 2.993 "
              "0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016c.896 0 "
              "1.699-.393 2.25-1.015a3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-"
              "4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 "
              "0 0 1-.621 4.72M6.75 18h3.75a.75.75 0 0 0 .75-.75V13.5a.75.75 0 0 0-.75-.75H6.75a"
              ".75.75 0 0 0-.75.75v3.75c0 .414.336.75.75.75Z",
    "serie": "M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25"
             "A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h"
             "-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605",
    "productos": "M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 "
                 "1.243-1.119 1.243H4.25a1.125 1.125 0 0 1-1.12-1.243l1.264-12A1.125 1.125 0 0 1 "
                 "5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007Z",
    "semana": "M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 "
              "0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 "
              "0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5",
    "eventos": "M3 3v1.5M3 21v-6m0 0 2.77-.693a9 9 0 0 1 6.208.682l.108.054a9 9 0 0 0 6.086.71l"
               "3.114-.732a48.524 48.524 0 0 1-.005-10.499l-3.11.732a9 9 0 0 1-6.085-.711l-.108"
               "-.054a9 9 0 0 0-6.208-.682L3 4.5M3 15V4.5",
    "mapa": "M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0ZM19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 "
            "17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z",
    "clima": "M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m"
             "-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1"
             "-7.5 0 3.75 3.75 0 0 1 7.5 0Z",
    "clientes": "M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 "
                "0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318"
                " 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 "
                "0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm"
                "8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z",
}

FUENTES_URL = "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400..800&display=swap"
# Lupa azul de la caja de búsqueda (fondo del campo; Streamlit no deja poner un icono dentro).
LUPA = "data:image/svg+xml;utf8," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" '
    f'stroke="#2563EB"><path stroke-linecap="round" stroke-linejoin="round" '
    f'd="{ICONOS["buscar"]}"/></svg>')

ESTILOS = """
<style>
@import url('__FUENTES__');
:root {
  --azul: #2563EB; --azul-claro: #EAF1FF; --azul-borde: #C9DAFB;
  --fondo: #EAF1FD; --hoja: #FFFFFF; --borde: #E3EAF6;
  --tinta: #0F172A; --texto: #1E293B; --texto-suave: #475569; --texto-tenue: #64748B;
  --verde: #059669; --rojo: #E11D48;
  --sombra: 0 1px 2px rgba(15, 23, 42, .04), 0 10px 30px -18px rgba(37, 99, 235, .30);
  --sombra-alta: 0 2px 4px rgba(15, 23, 42, .05), 0 22px 40px -20px rgba(37, 99, 235, .45);
  --radio: 1.25rem;
  --fuente: 'Plus Jakarta Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp, .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"],
.stApp button { font-family: var(--fuente) !important; }
.stApp { background: var(--fondo); color: var(--texto); -webkit-font-smoothing: antialiased; }
::selection { background: rgba(37, 99, 235, .18); color: var(--tinta); }
.stApp, .stApp * { scrollbar-width: thin; scrollbar-color: rgba(15, 23, 42, .2) transparent; }
/* La barra de Streamlit se oculta: la app tiene su propia barra superior */
[data-testid="stHeader"] { display: none; }
[data-testid="stMain"] { scroll-behavior: smooth; }
.block-container { max-width: 1560px; padding: 1.5rem 2rem 2.5rem; }

/* Barra superior: logo cuadrado, nombre y, a la derecha, el estado de los datos y la tienda */
.app-barra { display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  margin-bottom: 1.9rem; }
.logo { display: flex; align-items: center; gap: .75rem; text-decoration: none !important; }
.logo-cuadro { flex: none; width: 2.6rem; height: 2.6rem; border-radius: .75rem;
  display: grid; place-items: center; background: var(--azul); color: #FFFFFF;
  font-size: .9rem; font-weight: 800; letter-spacing: .02em;
  box-shadow: 0 6px 14px -6px rgba(37, 99, 235, .7); }
.logo b { display: block; font-size: 1.02rem; font-weight: 800; color: var(--tinta);
  line-height: 1.15; }
.logo small { display: block; font-size: .64rem; font-weight: 800; letter-spacing: .2em;
  color: var(--azul); }
.usuario { display: flex; align-items: center; gap: .8rem; }
.estado { display: inline-flex; align-items: center; gap: .45rem; padding: .5rem .9rem;
  border-radius: .75rem; background: var(--hoja); border: 1px solid var(--borde);
  font-size: .8rem; font-weight: 600; color: var(--texto-suave); box-shadow: var(--sombra); }
.estado i { width: .5rem; height: .5rem; border-radius: 9999px; background: var(--color); }
.avatar { flex: none; width: 2.35rem; height: 2.35rem; border-radius: 9999px; display: grid;
  place-items: center; background: var(--azul); color: #FFFFFF; font-weight: 800; }
.usuario b { font-size: .88rem; font-weight: 700; color: var(--tinta); }

/* Saludo: fecha, saludo con el nombre en azul y subtítulo */
.saludo { margin: 0 0 1.6rem; }
.saludo .fecha { display: flex; align-items: center; gap: .6rem; font-size: .85rem;
  font-weight: 700; color: var(--tinta); }
.saludo .fecha i { width: .38rem; height: .38rem; border-radius: 9999px;
  background: var(--azul); }
.saludo .fecha span { font-weight: 600; color: var(--azul); }
.saludo .hola { font-size: 2.35rem; font-weight: 800; letter-spacing: -.025em;
  line-height: 1.15; color: var(--tinta); margin: .6rem 0 .3rem; }
.saludo .hola em { font-style: normal; color: var(--azul); }
.saludo p { margin: 0; font-size: .98rem; font-weight: 500; color: var(--texto); }

/* Aviso de datos de demostración */
.aviso { display: flex; align-items: center; gap: .85rem; background: var(--hoja);
  border: 1px solid var(--borde); border-radius: 1rem; padding: .8rem 1.1rem;
  font-size: .9rem; line-height: 1.55; color: var(--texto-suave); box-shadow: var(--sombra);
  margin-bottom: 1.5rem; }
.insignia { flex: none; font-size: .72rem; font-weight: 700; padding: .25rem .7rem;
  border-radius: 9999px; color: #92400E; background: #FEF3C7; }

/* Tarjetas blancas: las del resumen (HTML) y las de Streamlit (key="tarjeta_...") */
.card, div[class*="st-key-tarjeta"] { background: var(--hoja); border: 1px solid var(--borde)
  !important; border-radius: var(--radio) !important; box-shadow: var(--sombra);
  animation: entrada .5s cubic-bezier(.22, 1, .36, 1) backwards; }
div[class*="st-key-tarjeta"] { padding: 1.35rem 1.45rem 1.25rem;
  transition: box-shadow .25s ease; }
div[class*="st-key-tarjeta"]:hover { box-shadow: var(--sombra-alta); }
@keyframes entrada { from { opacity: 0; transform: translateY(8px); } }

/* Pestañas de sección en la barra superior (la primera, Resumen, va marcada) */
.pestanas { display: flex; gap: .2rem; padding: .3rem; border-radius: 9999px;
  background: var(--hoja); border: 1px solid var(--borde); box-shadow: var(--sombra); }
.pestanas a { flex: none; font-size: .86rem; font-weight: 700; padding: .45rem 1.05rem;
  border-radius: 9999px; color: var(--texto) !important; text-decoration: none !important;
  transition: background .2s ease, color .2s ease; }
.pestanas a:hover { background: var(--azul-claro); color: var(--azul) !important; }
.pestanas a.activa { background: var(--azul); color: #FFFFFF !important;
  box-shadow: 0 6px 14px -8px rgba(37, 99, 235, .85); }

/* Bienvenida: saludo a la izquierda y tarjeta azul del informe a la derecha */
.bienvenida { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 31rem);
  align-items: center; gap: 1.5rem; margin-bottom: 1.5rem; }
.bienvenida .saludo { margin: 0; }
.cta { position: relative; overflow: hidden; display: flex; align-items: center; gap: 1rem;
  padding: 1.35rem 1.4rem; border-radius: var(--radio); color: #FFFFFF !important;
  text-decoration: none !important;
  background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 55%, #3B82F6 100%);
  box-shadow: 0 14px 30px -14px rgba(37, 99, 235, .75);
  transition: transform .2s ease, box-shadow .2s ease; }
.cta::before, .cta::after { content: ""; position: absolute; border-radius: 9999px;
  background: rgba(255, 255, 255, .09); pointer-events: none; }
.cta::before { width: 11rem; height: 11rem; right: -3rem; top: -4.5rem; }
.cta::after { width: 7rem; height: 7rem; right: 5rem; bottom: -4.5rem; }
.cta:hover { transform: translateY(-2px); box-shadow: 0 18px 34px -14px rgba(37, 99, 235, .85); }
.chip-cta { position: relative; flex: none; width: 3.1rem; height: 3.1rem; border-radius: .9rem;
  display: grid; place-items: center; color: #FFFFFF; background: rgba(255, 255, 255, .16);
  border: 1px solid rgba(255, 255, 255, .28); }
.chip-cta svg { width: 1.5rem; height: 1.5rem; }
.txt-cta { position: relative; min-width: 0; flex: 1; }
.txt-cta b { display: block; font-size: 1.25rem; font-weight: 800; letter-spacing: -.015em; }
.txt-cta span { display: block; margin-top: .15rem; font-size: .84rem; font-weight: 500;
  color: rgba(255, 255, 255, .9); }
.ir { position: relative; flex: none; width: 2.3rem; height: 2.3rem; border-radius: 9999px;
  display: grid; place-items: center; background: #FFFFFF; color: var(--azul); }
.ir svg { width: 1.1rem; height: 1.1rem; }

/* Indicadores del mes: 4 tarjetas en fila, cada una con su color de icono */
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1.25rem; }
.kpi { display: flex; flex-direction: column; padding: 1.2rem 1.3rem 1.1rem;
  transition: transform .2s ease, box-shadow .2s ease; }
.kpi:hover { transform: translateY(-2px); box-shadow: var(--sombra-alta); }
.kpi-cabeza { display: flex; align-items: center; gap: .65rem; font-size: .86rem;
  font-weight: 700; color: var(--texto-suave); }
.kpi-icono { flex: none; width: 2.3rem; height: 2.3rem; border-radius: .7rem; display: grid;
  place-items: center; color: var(--c); background: var(--f); }
.kpi-icono svg { width: 1.2rem; height: 1.2rem; }
.k-azul { --c: #2563EB; --f: #E8F1FF; } .k-lila { --c: #4F46E5; --f: #ECEEFF; }
.k-cian { --c: #0284C7; --f: #E0F2FE; } .k-gris { --c: #475569; --f: #EEF2F7; }
.kpi .valor { margin-top: .8rem; font-size: 2.1rem; font-weight: 800; letter-spacing: -.03em;
  line-height: 1.1; color: var(--tinta); font-variant-numeric: tabular-nums; }
.kpi .linea { display: flex; align-items: center; flex-wrap: wrap; gap: .5rem;
  margin-top: .45rem; font-size: .78rem; color: var(--texto-tenue); }
.kpi .detalle { margin-top: auto; padding-top: .75rem; border-top: 1px solid var(--borde);
  font-size: .82rem; color: var(--texto-suave); }
.kpi .linea + .detalle { margin-top: .85rem; }
.kpi .detalle b { font-weight: 700; color: var(--tinta); }
.cambio { display: inline-flex; align-items: center; gap: .25rem; font-size: .78rem;
  font-weight: 700; padding: .18rem .55rem; border-radius: 9999px;
  font-variant-numeric: tabular-nums; }
.cambio svg { width: .85em; height: .85em; }
.cambio.bien { color: var(--verde); background: #DCFCE7; }
.cambio.mal { color: var(--rojo); background: #FFE4E6; }

/* Fila de dos tarjetas: promedios por día y productos que más dejaron */
.duo { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.25rem;
  margin-top: 1.25rem; }
.duo .card { display: flex; flex-direction: column; padding: 1.3rem 1.4rem 1.2rem; }
.card-cabeza { display: flex; align-items: center; gap: .7rem; }
.card-cabeza b { font-size: 1.05rem; font-weight: 800; color: var(--tinta); }
.chip-icono, .tarjeta-icono { flex: none; width: 2.1rem; height: 2.1rem; border-radius: .65rem;
  display: grid; place-items: center; color: var(--azul); background: var(--azul-claro); }
.chip-icono svg, .tarjeta-icono svg { width: 1.15rem; height: 1.15rem; }
.pastilla { margin-left: auto; flex: none; font-size: .75rem; font-weight: 700;
  color: var(--texto-suave); background: #EEF2F8; border-radius: 9999px; padding: .3rem .75rem; }
.promedios { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem;
  margin-top: 1.1rem; }
.tile { min-width: 0; border-radius: .95rem; padding: .85rem 1rem .8rem; }
.tile.t-azul { background: #E8F1FF; --punto: #3B82F6; }
.tile.t-lila { background: #ECEEFF; --punto: #4F46E5; }
.tile.t-cian { background: #E0F2FE; --punto: #0284C7; }
.tile.t-gris { background: #F2F5F9; --punto: #94A3B8; }
.tile .rotulo { display: flex; align-items: center; gap: .45rem; font-size: .78rem;
  font-weight: 600; color: var(--texto-suave); white-space: nowrap; }
.tile .rotulo i { flex: none; width: .42rem; height: .42rem; border-radius: 9999px;
  background: var(--punto); }
.tile b { display: block; margin-top: .35rem; font-size: 1.4rem; font-weight: 800;
  letter-spacing: -.02em; color: var(--tinta); font-variant-numeric: tabular-nums; }
.chispa { display: flex; align-items: center; gap: .55rem; margin-top: 1.1rem;
  font-size: .86rem; color: var(--texto-suave); }
.chispa svg { flex: none; width: 1.1rem; height: 1.1rem; color: var(--azul); }
.chispa b { color: var(--tinta); }
.actualizado { display: flex; align-items: center; gap: .5rem; margin-top: auto;
  padding-top: .9rem; font-size: .76rem; font-weight: 600; color: var(--texto-tenue); }
.actualizado i { width: .45rem; height: .45rem; border-radius: 9999px;
  background: var(--azul); animation: pulso 2.4s ease-out infinite; }
@keyframes pulso { 0% { box-shadow: 0 0 0 0 rgba(37, 99, 235, .45); }
  80%, 100% { box-shadow: 0 0 0 .4rem rgba(37, 99, 235, 0); } }
/* Ficha de producto: su dibujo en su color sobre el mismo color muy claro; el número
   (si lo lleva) es su lugar en la lista */
.ficha { position: relative; flex: none; width: 2.35rem; height: 2.35rem; border-radius: .75rem;
  display: grid; place-items: center; color: var(--c);
  background: color-mix(in srgb, var(--c) 11%, #FFFFFF);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--c) 16%, transparent); }
.ficha svg { width: 1.45rem; height: 1.45rem; }
.ficha .rango { position: absolute; top: -.4rem; left: -.4rem; min-width: 1.05rem;
  height: 1.05rem; padding: 0 .2rem; border-radius: 9999px; display: grid; place-items: center;
  font-size: .62rem; font-weight: 800; color: #FFFFFF; background: var(--tinta);
  box-shadow: 0 0 0 2px var(--hoja); }
/* Lista de productos: ficha, nombre, barra de proporción y ganancia */
.top3 { display: flex; flex-direction: column; gap: .6rem; margin-top: 1.1rem; }
.fila { display: grid; align-items: center; gap: .8rem;
  grid-template-columns: 2.35rem minmax(0, 1.5fr) minmax(0, 1fr) 4.5rem; }
.fila .nom { font-size: .88rem; font-weight: 600; color: var(--texto); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.fila .prop { height: .45rem; border-radius: 9999px; background: #EEF3FF; overflow: hidden; }
.fila .prop i { display: block; height: 100%; border-radius: inherit;
  background: linear-gradient(90deg, #93B4F8, #2563EB); }
.fila b { text-align: right; font-size: .88rem; font-weight: 800; color: var(--tinta);
  font-variant-numeric: tabular-nums; }
.ver { margin-top: auto; padding-top: .9rem; display: inline-flex; align-items: center;
  gap: .35rem; align-self: flex-start; font-size: .82rem; font-weight: 700;
  color: var(--azul) !important; text-decoration: none !important; }
.ver svg { width: 1rem; height: 1rem; }

/* Accesos rápidos del inicio: una tarjeta por vista, con un dato clave y "Entrar" */
.accesos { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 1.25rem; }
.acceso { display: flex; flex-direction: column; gap: .35rem; padding: 1.3rem 1.3rem 1.15rem;
  color: var(--texto) !important; text-decoration: none !important;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease; }
.acceso:hover { transform: translateY(-3px); box-shadow: var(--sombra-alta);
  border-color: var(--azul-borde) !important; }
.acceso .chip-icono { width: 2.6rem; height: 2.6rem; border-radius: .8rem;
  margin-bottom: .45rem; }
.acceso .chip-icono svg { width: 1.35rem; height: 1.35rem; }
.acceso b { font-size: 1.02rem; font-weight: 800; color: var(--tinta); }
.acceso p { margin: 0; font-size: .84rem; line-height: 1.5; color: var(--texto-suave); }
.acceso .dato { align-self: flex-start; max-width: 100%; margin-top: .45rem; font-size: .74rem;
  font-weight: 700; color: var(--texto-suave); background: #EEF2F8; border-radius: 9999px;
  padding: .25rem .7rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.acceso .entrar { margin-top: auto; padding-top: .85rem; display: inline-flex;
  align-items: center; gap: .35rem; font-size: .85rem; font-weight: 800; color: var(--azul); }
.acceso .entrar svg { width: 1rem; height: 1rem; transition: transform .2s ease; }
.acceso:hover .entrar svg { transform: translateX(3px); }

/* Cabecera de cada vista: volver al resumen, icono, título y descripción */
.vista-cabeza { margin: .1rem 0 1.5rem; }
.volver { display: inline-flex; align-items: center; gap: .4rem; font-size: .84rem;
  font-weight: 700; color: var(--azul) !important; text-decoration: none !important;
  padding: .45rem .85rem .45rem .65rem; border-radius: .75rem; background: var(--hoja);
  border: 1px solid var(--borde); box-shadow: var(--sombra); transition: background .2s ease; }
.volver:hover { background: var(--azul-claro); }
.volver svg { width: 1rem; height: 1rem; }
.vista-titulo { display: flex; align-items: center; gap: 1rem; margin-top: 1.2rem; }
.vista-titulo .chip-icono { width: 3.2rem; height: 3.2rem; border-radius: 1rem;
  background: var(--hoja); border: 1px solid var(--borde); box-shadow: var(--sombra); }
.vista-titulo .chip-icono svg { width: 1.6rem; height: 1.6rem; }
.vista-titulo b { display: block; font-size: 2rem; font-weight: 800; letter-spacing: -.025em;
  line-height: 1.15; color: var(--tinta); }
.vista-titulo p { margin: .25rem 0 0; font-size: .95rem; color: var(--texto-suave); }
.vista-titulo .pastilla { align-self: flex-start; }

/* Informe del mes: periodo y botón de imprimir, hallazgos y listas de productos que cambian */
.acciones-informe { display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: .75rem; }
.acciones-informe .periodo { display: inline-flex; align-items: center; gap: .5rem;
  font-size: .88rem; font-weight: 600; color: var(--texto-suave); }
.acciones-informe .periodo svg { width: 1.1rem; height: 1.1rem; color: var(--azul); }
.acciones-informe .periodo b { color: var(--tinta); }
.imprimir { display: inline-flex; align-items: center; gap: .5rem; padding: .62rem 1.1rem;
  border: 0; border-radius: .8rem; background: var(--azul); color: #FFFFFF;
  font-family: var(--fuente); font-size: .86rem; font-weight: 700; cursor: pointer;
  box-shadow: 0 8px 18px -10px rgba(37, 99, 235, .9); transition: background .2s ease; }
.imprimir:hover { background: #1D4ED8; }
.imprimir:focus-visible { outline: 2px solid var(--azul); outline-offset: 3px; }
.imprimir svg { width: 1.1rem; height: 1.1rem; }
.saber { padding: 1.3rem 1.4rem 1.35rem; }
.hallazgos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .85rem;
  margin-top: 1.1rem; }
.hallazgo { display: flex; align-items: flex-start; gap: .8rem; padding: .95rem 1.05rem;
  border-radius: .95rem; background: var(--f); }
.hallazgo .h-icono { flex: none; width: 2.2rem; height: 2.2rem; border-radius: .7rem;
  display: grid; place-items: center; color: var(--c); background: #FFFFFF; }
.hallazgo .h-icono svg { width: 1.15rem; height: 1.15rem; }
.hallazgo p { margin: 0; align-self: center; font-size: .92rem; line-height: 1.55;
  color: var(--texto); }
.hallazgo p b { font-weight: 800; color: var(--tinta); }
.h-neutro { --c: #2563EB; --f: #EEF4FF; } .h-bien { --c: #059669; --f: #ECFDF5; }
.h-mal { --c: #E11D48; --f: #FFF1F2; }
.cambios { display: flex; flex-direction: column; gap: .6rem; margin-top: 1.1rem; }
.fila-cambio { display: grid; align-items: center; gap: .75rem; padding: .55rem .2rem;
  grid-template-columns: 2.35rem minmax(0, 1fr) auto 5.2rem;
  border-bottom: 1px solid var(--borde); }
.fila-cambio:last-child { border-bottom: 0; }
.fila-cambio .nom { font-size: .88rem; font-weight: 600; color: var(--texto); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.fila-cambio .por-dia { font-size: .8rem; color: var(--texto-tenue);
  font-variant-numeric: tabular-nums; }
.fila-cambio .cambio { justify-self: end; }
.tabla-precios td.prod { display: flex; align-items: center; gap: .75rem; }
.sin-cambios { margin: 1.1rem 0 0; font-size: .88rem; color: var(--texto-tenue); }

/* Precios del mercado: tabla de la mejor alternativa por producto */
.minis-precios { margin: 0; }
.tabla-envoltura { overflow-x: auto; margin: .4rem 0 .6rem; border: 1px solid var(--borde);
  border-radius: 1rem; }
/* En pantallas chicas la tabla conserva su ancho y se desliza dentro de su marco */
.tabla-precios { width: 100%; min-width: 62rem; border-collapse: collapse; font-size: .86rem; }
.tabla-precios td:first-child { min-width: 14rem; }
.tabla-precios td:nth-child(3), .tabla-precios td:last-child { min-width: 13rem; }
.tabla-precios th { text-align: left; font-size: .74rem; font-weight: 700; letter-spacing: .02em;
  text-transform: uppercase; color: var(--texto-tenue); background: #F6F9FF;
  padding: .7rem .9rem; white-space: nowrap; border-bottom: 1px solid var(--borde); }
.tabla-precios td { padding: .7rem .9rem; vertical-align: middle; color: var(--texto);
  border-bottom: 1px solid var(--borde); }
.tabla-precios tr:last-child td { border-bottom: 0; }
.tabla-precios tbody tr:hover td { background: #F8FAFF; }
.tabla-precios td b { font-weight: 700; color: var(--tinta); }
.tabla-precios td small { display: block; margin-top: .1rem; font-size: .76rem;
  color: var(--texto-tenue); }
.tabla-precios .num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums;
  font-weight: 700; color: var(--tinta); }
.tabla-precios .cambio { white-space: nowrap; }
.cambio.neutro { color: var(--texto-suave); background: #EEF2F8; }
.tabla-precios .propia { font-size: .8rem; color: var(--texto-suave); }
.tabla-precios .nada { color: var(--texto-tenue); }
.st-key-tarjeta_alternativas div.lectura .txt { white-space: normal; }

/* Buscador de productos: caja de búsqueda, ficha del resultado y "También" */
.st-key-buscar_precio { margin: .35rem 0 .2rem; }
.st-key-buscar_precio [data-testid="stTextInputRootElement"] {
  border: 1px solid var(--azul-borde) !important; border-radius: .9rem !important;
  background: #F6F9FF url("__LUPA__") no-repeat .95rem center / 1.15rem !important;
  min-height: 3rem; transition: border-color .2s ease, box-shadow .2s ease; }
.st-key-buscar_precio [data-testid="stTextInputRootElement"]:focus-within {
  border-color: var(--azul) !important; box-shadow: 0 0 0 4px rgba(37, 99, 235, .14); }
.st-key-buscar_precio input { background: transparent !important; padding-left: 2.7rem !important;
  font-size: .98rem; font-weight: 600; color: var(--tinta); }
.st-key-buscar_precio input::placeholder { color: var(--texto-tenue); font-weight: 500; }
.st-key-buscar_precio [data-testid="InputInstructions"] { display: none; }
.resultado-cabeza { display: flex; align-items: center; gap: 1rem; margin: 1.1rem 0 1rem; }
.resultado-cabeza > div { min-width: 0; }
.resultado-cabeza b { display: block; font-size: 1.25rem; font-weight: 800; color: var(--tinta);
  letter-spacing: -.01em; }
.resultado-cabeza small { display: block; margin-top: .1rem; font-size: .84rem;
  color: var(--texto-tenue); }
.quisiste { display: inline-block; margin-top: .35rem; font-size: .8rem;
  color: var(--texto-suave); }
.quisiste b { display: inline; font-size: inherit; color: var(--azul); }
.ficha.grande { width: 3.5rem; height: 3.5rem; border-radius: 1.05rem; }
.ficha.grande svg { width: 2.2rem; height: 2.2rem; }
.minis.cuatro { grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 0 0 .8rem; }
.minis.cuatro .mini b { font-size: 1.35rem; }
.mini small { display: block; margin-top: .25rem; font-size: .78rem; line-height: 1.45;
  color: var(--texto-suave); }
.mini small .cambio { margin-right: .25rem; }
.otros { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin-top: .2rem;
  font-size: .82rem; color: var(--texto-tenue); }
.otro { display: inline-flex; align-items: center; gap: .45rem;
  padding: .25rem .75rem .25rem .25rem; border-radius: 9999px; background: #F6F9FF;
  border: 1px solid var(--borde); font-weight: 700; color: var(--texto) !important;
  text-decoration: none !important;
  transition: border-color .2s ease, background .2s ease; }
.otro:hover { border-color: var(--azul-borde); background: var(--azul-claro); }
.otro .ficha { width: 1.7rem; height: 1.7rem; border-radius: 9999px; }
.otro .ficha svg { width: 1.05rem; height: 1.05rem; }
.sin-resultados { margin: .9rem 0 .2rem; font-size: .9rem; color: var(--texto-suave); }
.filtrada { margin: .2rem 0 .5rem; font-size: .84rem; font-weight: 600; color: var(--azul); }

/* Anterior y siguiente al final de cada vista */
.pasos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.25rem;
  margin-top: 1.75rem; }
.paso { display: flex; flex-direction: column; gap: .2rem; padding: 1rem 1.2rem;
  color: var(--texto) !important; text-decoration: none !important;
  transition: box-shadow .2s ease, border-color .2s ease; }
.paso:hover { box-shadow: var(--sombra-alta); border-color: var(--azul-borde) !important; }
.paso span { display: inline-flex; align-items: center; gap: .3rem; font-size: .76rem;
  font-weight: 700; color: var(--azul); }
.paso span svg { width: .95rem; height: .95rem; }
.paso b { font-size: 1rem; font-weight: 800; color: var(--tinta); }
.paso.sig { grid-column: 2; align-items: flex-end; text-align: right; }

/* Encabezados de sección: barrita azul y título en negrita */
div.bloque { display: flex; align-items: center; gap: .6rem; margin: 2.3rem 0 .95rem;
  scroll-margin-top: 5rem; font-size: 1.15rem; font-weight: 800; letter-spacing: -.01em;
  color: var(--tinta); }
div.bloque::before { content: ""; width: 4px; height: 1.25rem; border-radius: 4px;
  background: var(--azul); }

/* Cabecera de las tarjetas de gráficas: icono, título y descarga en CSV a la derecha */
div.tarjeta-titulo { display: flex; align-items: center; gap: .7rem; scroll-margin-top: 5rem; }
div.tarjeta-titulo .texto { min-width: 0; font-size: 1.05rem; font-weight: 800;
  color: var(--tinta); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
div.tarjeta-titulo .accion { margin-left: auto; flex: none; display: inline-flex;
  align-items: center; gap: .3rem; font-size: .8rem; font-weight: 700;
  color: var(--azul) !important; text-decoration: none !important; padding: .3rem .55rem;
  border-radius: .6rem; transition: background .2s ease; }
div.tarjeta-titulo .accion:hover { background: var(--azul-claro); }
div.tarjeta-titulo .accion svg { width: .95rem; height: .95rem; }
div.tarjeta-nota { font-size: .84rem; color: var(--texto-tenue); line-height: 1.45;
  margin: .45rem 0 .5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.punto { display: inline-block; width: .55rem; height: .55rem; border-radius: 9999px;
  margin: 0 .35rem 0 .35rem; vertical-align: .03rem; }
.raya { display: inline-block; width: 1.1rem; border-top: 2px dashed #64748B;
  margin: 0 .35rem 0 .45rem; vertical-align: .22rem; }
.st-key-tarjeta_venta_dia { margin-bottom: 1rem; }

/* Selector de rango tipo pastilla: riel azul muy claro y la opción elegida en azul */
.st-key-rango_venta { margin: .1rem 0 .3rem; }
.st-key-rango_venta div:has(> button[role="radio"]) { display: inline-flex; gap: .2rem;
  padding: .25rem; border-radius: 9999px; background: #EEF3FF; border: 0; }
.st-key-rango_venta button[role="radio"] { border: 0 !important;
  border-radius: 9999px !important; background: transparent; box-shadow: none; min-height: 0;
  padding: .42rem 1.2rem; font-size: .85rem; font-weight: 700; color: var(--texto);
  transition: background .2s ease, color .2s ease; }
.st-key-rango_venta button[role="radio"]:hover { color: var(--azul); }
.st-key-rango_venta button[aria-checked="true"] { color: #FFFFFF !important;
  background: var(--azul) !important; box-shadow: 0 6px 14px -8px rgba(37, 99, 235, .85); }
.st-key-rango_venta button[aria-checked="true"] * { color: #FFFFFF !important; }

/* Lectura al pie de cada gráfica: chispa azul y texto sobre azul muy claro */
div.lectura { display: flex; align-items: center; gap: .6rem; margin-top: .3rem;
  box-sizing: border-box; padding: .7rem .95rem; border-radius: .85rem; background: #F3F7FF;
  font-size: .88rem; line-height: 1.5; color: var(--texto-suave); }
div.lectura .foco { flex: none; display: grid; color: var(--azul); }
div.lectura .foco svg { width: 1.1rem; height: 1.1rem; }
div.lectura .txt { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
div.lectura b { font-weight: 700; color: var(--tinta); }

/* Estado vacío */
.vacio { display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: .55rem; text-align: center; min-height: 320px; padding: 1.5rem 1rem; }
.vacio-icono { width: 3.3rem; height: 3.3rem; border-radius: 9999px; display: grid;
  place-items: center; color: var(--azul); background: var(--azul-claro); }
.vacio-icono svg { width: 1.5rem; height: 1.5rem; }
.vacio b { font-size: 1.05rem; font-weight: 800; color: var(--tinta); }
.vacio p { margin: 0; max-width: 36ch; font-size: .88rem; line-height: 1.55;
  color: var(--texto-tenue); }
.vacio code, .aviso code { color: var(--tinta); background: #F1F5F9; }

/* Mini indicadores del mapa: fichas de color como las del resumen */
.minis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .85rem;
  margin: .6rem 0 .9rem; }
.mini { border-radius: .95rem; padding: .8rem 1rem; background: #E8F1FF; --punto: #3B82F6; }
.mini:nth-child(2) { background: #ECEEFF; --punto: #4F46E5; }
.mini:nth-child(3) { background: #F2F5F9; --punto: #94A3B8; }
.mini > span { display: flex; align-items: center; gap: .45rem; font-size: .78rem;
  font-weight: 600; color: var(--texto-suave); }
.mini > span::before { content: ""; flex: none; width: .42rem; height: .42rem;
  border-radius: 9999px; background: var(--punto); }
.mini b { display: block; margin-top: .3rem; font-size: 1.6rem; font-weight: 800;
  color: var(--tinta); font-variant-numeric: tabular-nums; }
.st-key-tarjeta_mapa [data-testid="stDeckGlJsonChart"] { border-radius: 1rem;
  overflow: hidden; border: 1px solid var(--borde); }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--texto-tenue) !important; }

/* Globos de ayuda de las gráficas (Vega) */
#vg-tooltip-element, .vg-tooltip { font-family: var(--fuente) !important;
  background: #FFFFFF !important; color: var(--texto) !important;
  border: 1px solid var(--borde) !important; border-radius: .75rem !important;
  box-shadow: 0 14px 30px -14px rgba(37, 99, 235, .45) !important;
  padding: .55rem .8rem !important; font-size: .84rem !important; }
#vg-tooltip-element td.key, .vg-tooltip td.key { color: var(--texto-tenue) !important; }
#vg-tooltip-element td.value, .vg-tooltip td.value { color: var(--tinta) !important;
  font-weight: 700; }

/* Barra fija: aparece al bajar (animación ligada al desplazamiento, solo CSS). Donde el
   navegador no la soporta, simplemente no aparece. */
[data-testid="stMain"] { scroll-timeline: --pagina block; }
.barra { position: fixed; top: .75rem; left: 50%; z-index: 999991;
  width: min(1180px, calc(100% - 2rem)); display: flex; align-items: center;
  justify-content: space-between; gap: 1rem; padding: .45rem .55rem .45rem .5rem;
  border-radius: 1rem; background: rgba(255, 255, 255, .9); border: 1px solid var(--borde);
  -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px);
  box-shadow: 0 12px 30px -16px rgba(37, 99, 235, .45);
  transform: translate(-50%, -160%); opacity: 0; visibility: hidden; }
@supports (animation-timeline: --pagina) {
  .barra { animation: barra-aparece linear both; animation-timeline: --pagina;
    animation-range: 260px 340px; } }
@keyframes barra-aparece { to { transform: translate(-50%, 0); opacity: 1;
  visibility: visible; } }
.barra .logo-cuadro { width: 2.1rem; height: 2.1rem; border-radius: .6rem; font-size: .72rem; }
.barra .logo b { font-size: .92rem; }
.barra-indice { display: flex; gap: .2rem; min-width: 0; overflow-x: auto;
  scrollbar-width: none; }
.barra-indice a { flex: none; font-size: .84rem; font-weight: 700; padding: .4rem .8rem;
  border-radius: .7rem; color: var(--texto) !important; text-decoration: none !important;
  transition: background .2s ease, color .2s ease; }
.barra-indice a:hover, .barra-indice a.activa { background: var(--azul-claro);
  color: var(--azul) !important; }
.barra-mes { flex: none; font-size: .75rem; font-weight: 700; color: var(--azul);
  background: var(--azul-claro); padding: .35rem .75rem; border-radius: 9999px; }

/* Pie de página */
div.pie { margin-top: 2.6rem; padding: 1.6rem 1rem .6rem; text-align: center;
  border-top: 1px solid #D6E0F0; font-size: .82rem; line-height: 1.8;
  color: var(--texto-tenue); }
.pie .logo { justify-content: center; margin-bottom: .5rem; }
.pie .logo-cuadro { width: 2rem; height: 2rem; border-radius: .6rem; font-size: .7rem; }
div.pie i { display: inline-block; width: .28rem; height: .28rem; margin: 0 .6rem;
  border-radius: 9999px; vertical-align: .18rem; background: #94A3B8; }
.pie .arriba { display: inline-flex; align-items: center; gap: .35rem; margin-top: .9rem;
  padding: .45rem 1rem; border-radius: .75rem; font-weight: 700;
  color: var(--azul) !important; text-decoration: none !important;
  background: var(--azul-claro); transition: background .2s ease; }
.pie .arriba:hover { background: #DCE8FE; }
.app-barra { scroll-margin-top: 1rem; }

/* Foco visible al navegar con el teclado */
.cta:focus-visible, .pestanas a:focus-visible, .ver:focus-visible, .acceso:focus-visible,
.volver:focus-visible, .paso:focus-visible, .barra-indice a:focus-visible,
.pie .arriba:focus-visible, div.tarjeta-titulo .accion:focus-visible,
.st-key-rango_venta button:focus-visible { outline: 2px solid var(--azul);
  outline-offset: 3px; }

/* Pantallas medianas y chicas: notas y lecturas pueden ocupar dos líneas y todas reservan
   dos, para que las tarjetas de una fila sigan parejas. */
@media (max-width: 2000px) {
  div.lectura .txt { white-space: normal; }
  div.lectura { min-height: 4.6em; } }
@media (max-width: 1600px) {
  div.tarjeta-nota { white-space: normal; min-height: 2.9em; } }
@media (max-width: 1300px) { .usuario b { display: none; }
  div.tarjeta-titulo .texto { white-space: normal; }
  .accesos { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
/* Con 7 pestañas la barra no cabe: fuera el estado (el aviso del resumen ya lo dice) y
   pestañas más compactas */
@media (max-width: 1600px) { .app-barra .estado { display: none; } }
@media (max-width: 1300px) { .pestanas a { padding: .45rem .8rem; font-size: .84rem; } }
@media (max-width: 1100px) { .pestanas a { padding: .42rem .6rem; font-size: .8rem; }
  .app-barra .logo > span:last-child { display: none; } }
@media (max-width: 1100px) { .kpis, .accesos, .minis.cuatro {
    grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bienvenida { grid-template-columns: 1fr; } }
@media (max-width: 900px) {
  .app-barra { flex-wrap: wrap; row-gap: .9rem; margin-bottom: 1.5rem; }
  .app-barra .pestanas { order: 3; flex: 1 0 100%; overflow-x: auto; scrollbar-width: none;
    border-radius: 1rem; scroll-snap-type: x proximity; }
  .app-barra .pestanas::-webkit-scrollbar { display: none; }
  .app-barra .pestanas a { scroll-snap-align: center; padding: .45rem .85rem;
    font-size: .84rem; }
  .app-barra .logo > span:last-child { display: block; }
  .duo { grid-template-columns: 1fr; } }
@media (max-width: 640px) {
  .block-container { padding: 1rem 1rem 2rem; }
  .app-barra .estado, .usuario b { display: none; }
  .saludo .hola { font-size: 1.75rem; }
  .kpis, .minis, .minis.cuatro, .accesos, .pasos, .hallazgos { grid-template-columns: 1fr; }
  .resultado-cabeza .pastilla { display: none; }
  .fila-cambio { grid-template-columns: 2.35rem minmax(0, 1fr) 5.2rem; }
  .fila-cambio .por-dia { display: none; }
  .tabla-envoltura { border: 0; overflow: visible; }
  .tabla-precios { min-width: 0; }
  .tabla-precios thead { display: none; }
  /* Orden en la tarjeta: producto; tu costo y precio lado a lado; dónde; si conviene */
  .tabla-precios tr { display: grid; grid-template-columns: 1fr 1fr; gap: .6rem .9rem;
    padding: .9rem 1rem; margin-bottom: .7rem; border: 1px solid var(--borde);
    border-radius: 1rem; }
  .tabla-precios tbody tr:hover td { background: transparent; }
  .tabla-precios td { display: block; padding: 0; border: 0; min-width: 0 !important; }
  .tabla-precios td.prod { grid-column: 1 / -1; display: flex; }
  .tabla-precios td:nth-child(2) { order: 1; } .tabla-precios td:nth-child(4) { order: 2; }
  .tabla-precios td:nth-child(3) { order: 3; grid-column: 1 / -1; }
  .tabla-precios td.conviene { order: 4; grid-column: 1 / -1; }
  .tabla-precios td:last-child { order: 5; grid-column: 1 / -1; }
  .tabla-precios td.conviene[data-etiqueta]::before, .tabla-precios td.sin-propia {
    display: none; }
  .fila { grid-template-columns: 2.35rem minmax(0, 1fr) auto; }
  .fila .prop { display: none; }
  .tabla-precios td[data-etiqueta]::before { content: attr(data-etiqueta); display: block;
    margin-bottom: .15rem; font-size: .68rem; font-weight: 700; letter-spacing: .03em;
    text-transform: uppercase; color: var(--texto-tenue); }
  .tabla-precios .num { text-align: left; }
  .paso.sig { grid-column: auto; }
  .vista-titulo b { font-size: 1.5rem; } .vista-titulo .pastilla { display: none; }
  .aviso { flex-direction: column; align-items: flex-start; gap: .5rem; }
  div.tarjeta-titulo .texto { white-space: normal; }
  div.tarjeta-nota, div.lectura { min-height: 0; }
  .barra-mes, .barra .logo > span:last-child { display: none; }
  .barra-indice a { padding: .35rem .55rem; font-size: .78rem; }
  .barra-indice { -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 1.2rem),
    transparent); mask-image: linear-gradient(90deg, #000 calc(100% - 1.2rem), transparent); }
  .st-key-rango_venta button[role="radio"] { padding: .38rem .75rem; }
  @supports (animation-timeline: --pagina) { .barra { animation-range: 300px 380px; } } }
@media (prefers-reduced-motion: reduce) {
  .card, div[class*="st-key-tarjeta"], .actualizado i { animation: none !important; }
  .cta, .kpi, .acceso, .acceso .entrar svg, div[class*="st-key-tarjeta"] { transition: none; }
  .cta:hover, .kpi:hover, .acceso:hover { transform: none; }
  [data-testid="stMain"] { scroll-behavior: auto; } }
/* Impresión (Ctrl+P o "Guardar como PDF"): fondo blanco, sin sombras ni controles, y las
   tarjetas no se parten entre páginas */
@media print {
  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #FFFFFF !important; }
  .card, .aviso, div[class*="st-key-tarjeta"] { box-shadow: none !important;
    animation: none !important; break-inside: avoid; }
  .cta, .logo-cuadro, .avatar, .tile, .mini, .cambio, .kpi-icono, .hallazgo, .ficha {
    -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .barra, .pestanas, .ver, .volver, .pasos, .accesos, .pie .arriba, .st-key-rango_venta, .imprimir,
  [data-testid="stElementToolbar"], .tarjeta-titulo .accion { display: none !important; }
  div.bloque { break-after: avoid; } }
</style>
""".replace("__FUENTES__", FUENTES_URL).replace("__LUPA__", LUPA)

st.set_page_config(page_title="AbarrotesPOS", page_icon=":material/storefront:",
                   layout="wide")
st.markdown(ESTILOS, unsafe_allow_html=True)


def html(codigo):
    st.markdown(codigo, unsafe_allow_html=True)


def punto(*colores):
    """Punto de leyenda; con varios colores se pinta como degradado."""
    fondo = colores[0] if len(colores) == 1 else f"linear-gradient(90deg, {', '.join(colores)})"
    return f'<span class="punto" style="background:{fondo}"></span>'


def logo(sub="TABLERO"):
    return (f'<span class="logo"><span class="logo-cuadro">AP</span><span><b>Abarrotes POS</b>'
            f"<small>{sub}</small></span></span>")


def ir(clave):
    """Atributos de un enlace a otra vista del tablero (abre en la misma pestaña)."""
    return f'href="?vista={clave}" target="_self"'


def cabecera_vista(clave):
    """Cabecera de una vista de detalle: volver al resumen, icono, título y descripción."""
    _, dibujo, titulo, desc = VISTAS[clave]
    html(f'<div class="vista-cabeza"><a class="volver" {ir("inicio")}>{icono("atras", 2)}'
         f'Volver al resumen</a><div class="vista-titulo"><span class="chip-icono">'
         f'{icono(dibujo)}</span><div><b>{titulo}</b><p>{desc}</p></div>'
         f'<span class="pastilla">{nombre_mes}</span></div></div>')


def pasos(clave):
    """Botones a la vista anterior y a la siguiente, al final de cada vista de detalle."""
    orden = list(VISTAS)[1:]
    i = orden.index(clave)
    partes = []
    if i > 0:
        partes.append(f'<a class="card paso" {ir(orden[i - 1])}><span>{icono("atras", 2)}'
                      f'Anterior</span><b>{VISTAS[orden[i - 1]][2]}</b></a>')
    if i < len(orden) - 1:
        partes.append(f'<a class="card paso sig" {ir(orden[i + 1])}><span>Siguiente'
                      f'{icono("flecha", 2)}</span><b>{VISTAS[orden[i + 1]][2]}</b></a>')
    html(f'<nav class="pasos">{"".join(partes)}</nav>')


def bloque(numero, texto, extra=""):
    """Encabezado de sección: barrita azul, título en negrita y, opcional, una pastilla a la
    derecha."""
    html(f'<div class="bloque" id="seccion-{numero}">{texto}{extra}</div>')


def titulo_tarjeta(dibujo, titulo, nota="", descarga=None):
    """Icono + título + nota de una línea (todas las tarjetas arrancan su gráfica a la misma
    altura). El título lleva el ancla "t-<icono>" para los enlaces del resumen. Con
    descarga=(tabla, archivo), a la derecha va un enlace que baja esos datos en CSV (el archivo
    viaja dentro del enlace; no hace falta servidor)."""
    accion = ""
    if descarga is not None:
        tabla, archivo = descarga
        csv = quote(tabla.to_csv(index=False))
        accion = (f'<a class="accion" download="{archivo}" title="Descargar los datos en CSV" '
                  f'href="data:text/csv;charset=utf-8,{csv}">{icono("descarga", 2)}CSV</a>')
    html(f'<div class="tarjeta-titulo" id="t-{dibujo}"><span class="tarjeta-icono">'
         f'{icono(dibujo)}</span><span class="texto">{titulo}</span>{accion}</div>'
         f'<div class="tarjeta-nota">{nota or "&nbsp;"}</div>')


def vacio(dibujo, titulo, texto):
    """Estado vacío: icono en círculo, título y explicación, en lugar de una gráfica en blanco."""
    html(f'<div class="vacio"><span class="vacio-icono">{icono(dibujo)}</span>'
         f'<b>{titulo}</b><p>{texto}</p></div>')


def lectura(texto):
    """Interpretación de una línea al pie de la gráfica (admite <b>)."""
    html(f'<div class="lectura"><span class="foco">{icono("chispa")}</span>'
         f'<span class="txt">{texto}</span></div>')


def icono(nombre, grosor=1.6):
    return ('<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
            f'stroke-width="{grosor}" stroke="currentColor" aria-hidden="true">'
            f'<path stroke-linecap="round" stroke-linejoin="round" d="{ICONOS[nombre]}"/></svg>')


def degradado(*colores, vertical=False):
    """Relleno degradado para barras (Vega-Lite): los colores se reparten parejo de inicio a fin.
    Horizontal va de izquierda a derecha; vertical, de abajo hacia arriba."""
    paradas = [alt.GradientStop(color=c, offset=i / (len(colores) - 1))
               for i, c in enumerate(colores)]
    return alt.Gradient(gradient="linear", x1=0, y1=1 if vertical else 0, x2=0 if vertical else 1,
                        y2=0, stops=paradas)


def dinero(campo, titulo):
    """Renglón de globo de ayuda con una cifra en pesos."""
    return alt.Tooltip(f"{campo}:Q", title=titulo, format="$,.0f")


def cifras(base, campo, vertical=False):
    """Cifra en pesos al final de cada barra: a la derecha (horizontales) o encima (verticales)."""
    lugar = ({"align": "center", "baseline": "bottom", "dy": -6} if vertical
             else {"align": "left", "baseline": "middle", "dx": 6})
    return base.mark_text(color=TEXTO, fontSize=12, fontWeight=700, **lugar).encode(
        text=alt.Text(f"{campo}:Q", format="$,.0f"))


def resalte(campo):
    """Selección al pasar el cursor + opacidad: la barra señalada queda plena y las demás se
    atenúan. Sin cursor encima, todas se ven completas."""
    sel = alt.selection_point(on="pointerover", clear="pointerout", fields=[campo])
    return sel, alt.when(sel).then(alt.value(1.0)).otherwise(alt.value(0.35))


def con_fichas(datos, campo="producto"):
    """Columna "ficha" con el dibujo de cada producto y el nombre ya con acentos."""
    return datos.assign(ficha=datos[campo].map(imagen), **{campo: datos[campo].map(nombre)})


def fichas_en_eje(datos, eje_y):
    """Capa con el dibujo de cada producto a la izquierda de su nombre (el eje deja el hueco
    con labelPadding)."""
    return alt.Chart(datos).mark_image(width=20, height=20, align="center",
                                       baseline="middle").encode(
        y=eje_y, x=alt.value(-16), url="ficha:N")


def barras_horizontales(datos, valor, nombre, tooltip, color, fichas=False):
    """Barras horizontales de mayor a menor con su cifra al final (deja aire a la derecha),
    renglones alternos sombreados y un rombo ámbar en el primer lugar. Con fichas=True, cada
    renglón lleva el dibujo de su producto (columna "ficha", ver con_fichas)."""
    datos = datos.sort_values(valor, ascending=False).reset_index(drop=True)
    tope = datos[valor].max() * 1.22
    eje_y = alt.Y(f"{nombre}:N", sort=list(datos[nombre]), title=None,
                  axis=alt.Axis(labelPadding=32) if fichas else alt.Undefined)
    base = alt.Chart(datos).encode(
        x=alt.X(f"{valor}:Q", title=None, axis=alt.Axis(format="$,.0f"),
                scale=alt.Scale(domainMax=tope)),
        y=eje_y, tooltip=tooltip)
    renglones = alt.Chart(datos.iloc[1::2]).mark_rect(color=AZUL, opacity=.04).encode(
        y=eje_y, x=alt.datum(0), x2=alt.datum(tope))
    primero = alt.Chart(datos.head(1)).mark_point(
        shape="diamond", filled=True, size=90, color=AMBAR, stroke="white", strokeWidth=1.5,
        opacity=1).encode(y=eje_y, x=alt.datum(datos[valor].max() * .035))
    sel, opacidad = resalte(nombre)
    capas = (renglones + base.mark_bar(cornerRadiusEnd=5).encode(color=color, opacity=opacidad)
             .add_params(sel) + primero + cifras(base, valor))
    return capas + fichas_en_eje(datos, eje_y) if fichas else capas


def estilo(grafica, alto):
    # contains="padding": las etiquetas del eje cuentan dentro del ancho (no se cortan en celular).
    return (grafica.properties(height=alto, background="transparent",
                               padding={"left": 18, "right": 8},
                               autosize=alt.AutoSizeParams(type="fit", contains="padding"))
            .configure(font=FUENTE)
            .configure_view(stroke=None)
            .configure_axis(labelColor=TEXTO_EJE, gridColor=REJILLA, domain=False, ticks=False,
                            labelFontSize=12, labelPadding=6, labelLimit=170)
            .configure_axisQuantitative(tickCount=5)
            .configure_bar(opacity=0.95))


def rgb(color, alfa=255):
    """'#7AA2F7' -> [122, 162, 247, 255] (formato de color de pydeck)."""
    return [int(color[i:i + 2], 16) for i in (1, 3, 5)] + [alfa]


def pesos(x):
    return f"${x:,.0f}"


def tendencia(actual, anterior, sube_es_bueno=True):
    """Chip con flecha y '3.2 %' contra el mismo tramo del mes anterior ('' si no hay con qué
    comparar)."""
    if not anterior:
        return ""
    cambio = (actual - anterior) / anterior * 100
    bien = (cambio >= 0) == sube_es_bueno
    return (f'<span class="cambio {"bien" if bien else "mal"}">'
            f'{icono("sube" if cambio >= 0 else "baja", 2.2)}{abs(cambio):.1f} %</span>')


def leer(ruta):
    """CSV opcional: tabla vacía si todavía no se ha generado."""
    return pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()


# --- Datos ----------------------------------------------------------------------------------
diarias = pd.read_csv(ORO / "ventas_diarias.csv", parse_dates=["fecha"])
producto = pd.read_csv(ORO / "ventas_producto_mes.csv")
tiendas = leer(PLATA / "tiendas_zona.csv")
competencia = leer(ORO / "competencia_tienda_piloto.csv")
fiados = leer(ORO / "fiados_por_cliente.csv")
comparativo = leer(ORO / "comparativo_precios.csv")
cadenas = leer(ORO / "precios_por_cadena.csv")

ultimo_mes = diarias["fecha"].max().to_period("M")
mes = diarias[diarias["fecha"].dt.to_period("M") == ultimo_mes]
nombre_mes = f"{MESES[ultimo_mes.month - 1]} {ultimo_mes.year}"
periodo = (f"Del {mes['fecha'].min().day} al {mes['fecha'].max().day} de {nombre_mes}"
           if len(mes) else nombre_mes)
# Comparación justa: los mismos días del mes anterior (p. ej. 1-15 nov contra 1-15 oct).
mes_ant = ultimo_mes - 1
ultimo_dia = mes["fecha"].dt.day.max() if len(mes) else 31
anterior = diarias[(diarias["fecha"].dt.to_period("M") == mes_ant)
                   & (diarias["fecha"].dt.day <= ultimo_dia)]
vs = f"{anterior['fecha'].dt.day.min()}–{ultimo_dia} {MESES[mes_ant.month - 1][:3]}"
demo = bool((diarias["fuente"] == "pos_demo").all())

# --- Barra superior y saludo ----------------------------------------------------------------
# Fecha y saludo según la hora del servidor; "actualizado" es cuándo corrió el pipeline por
# última vez (fecha del archivo de oro).
ahora = datetime.now()
saludo = ("Buenos días" if ahora.hour < 12 else "Buenas tardes" if ahora.hour < 19
          else "Buenas noches")
hoy = f"{DIAS_LARGOS[ahora.weekday()].capitalize()} {ahora.day} de {MESES[ahora.month - 1]}"
hecho = datetime.fromtimestamp((ORO / "ventas_diarias.csv").stat().st_mtime)
actualizado = f"{hecho.day} {MESES[hecho.month - 1][:3]} {hecho.year}, {hecho:%H:%M}"
estado = ('<span class="estado" style="--color:#F59E0B"><i></i>Datos de demostración</span>'
          if demo else '<span class="estado" style="--color:#059669"><i></i>Datos reales</span>')
tienda = TIENDA_PILOTO["nombre"]
vista = st.query_params.get("vista", "inicio")
if vista not in VISTAS:
    vista = "inicio"
activa = ' class="activa"'
indice = "".join(f'<a {ir(c)}{activa if c == vista else ""}>{datos[0]}</a>'
                 for c, datos in VISTAS.items())
bienvenida = f"""
<div class="bienvenida">
  <div class="saludo">
    <div class="fecha">{hoy}<i></i><span>Dueño</span></div>
    <div class="hola">{saludo}, <em>Dueño</em></div>
    <p>Así va tu tienda en {nombre_mes}.</p>
  </div>
  <a class="cta" {ir("informe")}><span class="chip-cta">{icono("informe")}</span>
    <span class="txt-cta"><b>Informe de {nombre_mes}</b><span>{periodo}</span>
    </span><span class="ir">{icono("flecha", 2)}</span></a>
</div>""" if vista == "inicio" else ""
html(f"""
<div class="app-barra" id="inicio">
  {logo()}
  <nav class="pestanas" aria-label="Secciones del tablero">{indice}</nav>
  <div class="usuario">{estado}<span class="avatar">{tienda[0]}</span><b>{tienda}</b></div>
</div>
{bienvenida}
<nav class="barra" aria-label="Secciones del tablero">
  {logo()}
  <span class="barra-indice">{indice}</span>
  <span class="barra-mes">{nombre_mes}</span>
</nav>
""")

# --- Inicio: resumen del mes y accesos rápidos ------------------------------------------
if vista == "inicio":
    if demo:
        html('<div class="aviso"><span class="insignia">Demostración</span><span>Las ventas son '
             "simuladas y se reemplazan por las reales de la tienda piloto en cuanto el dueño las "
             "comparta. El clima y el mapa sí son datos reales.</span></div>")

    # --- I. Resumen del mes: 4 indicadores, promedios por día y productos que más dejaron ------
    bloque("I", f"Resumen de {nombre_mes}", f'<span class="pastilla">vs {vs}</span>')
    venta, ganancia = mes["venta"].sum(), mes["ganancia"].sum()
    tickets, fiado = mes["tickets"].sum(), mes["venta_fiado"].sum()
    margen = ganancia / venta * 100 if venta else 0
    ticket_prom = venta / tickets if tickets else 0
    parte_fiado = fiado / venta * 100 if venta else 0
    dias_mes = max(mes["fecha"].nunique(), 1)
    # (color, icono, etiqueta, cifra, chip de tendencia, detalle). Que el fiado suba no es bueno.
    indicadores = [
        ("k-azul", "venta", "Venta", pesos(venta), tendencia(venta, anterior["venta"].sum()),
         "Total cobrado en el periodo"),
        ("k-lila", "ganancia", "Ganancia", pesos(ganancia),
         tendencia(ganancia, anterior["ganancia"].sum()), f"Margen de <b>{margen:.1f} %</b>"),
        ("k-cian", "tickets", "Tickets", f"{tickets:,}",
         tendencia(tickets, anterior["tickets"].sum()),
         f"Ticket promedio de <b>{pesos(ticket_prom)}</b>"),
        ("k-gris", "fiado", "Vendido a fiado", pesos(fiado),
         tendencia(fiado, anterior["venta_fiado"].sum(), sube_es_bueno=False),
         f"<b>{parte_fiado:.1f} %</b> de la venta, por cobrar"),
    ]
    tarjetas = "".join(
        f'<div class="card kpi {color}"><div class="kpi-cabeza"><span class="kpi-icono">'
        f'{icono(clave)}</span>{etiqueta}</div><div class="valor">{cifra}</div>'
        f'<div class="linea">{chip}<span>vs {vs}</span></div><div class="detalle">{detalle}</div>'
        "</div>"
        for color, clave, etiqueta, cifra, chip, detalle in indicadores)
    promedios = [("t-azul", "Venta por día", pesos(venta / dias_mes)),
                 ("t-lila", "Mejor día", pesos(mes["venta"].max() if len(mes) else 0)),
                 ("t-cian", "Ganancia por día", pesos(ganancia / dias_mes)),
                 ("t-gris", "Tickets por día", f"{tickets / dias_mes:,.0f}")]
    top5 = producto[producto["mes"] == str(ultimo_mes)].nlargest(5, "ganancia")
    filas_top = "".join(
        f'<div class="fila">{ficha(p["producto"], n)}'
        f'<span class="nom">{nombre(p["producto"])}</span>'
        f'<span class="prop"><i style="width:{p["ganancia"] / top5["ganancia"].max() * 100:.0f}%">'
        f'</i></span><b>{pesos(p["ganancia"])}</b></div>'
        for n, (_, p) in enumerate(top5.iterrows(), start=1))
    html(f"""
<div class="kpis">{tarjetas}</div>
<div class="duo">
  <div class="card">
    <div class="card-cabeza"><span class="chip-icono">{icono("barras")}</span>
      <b>Promedios por día</b><span class="pastilla">{dias_mes} días</span></div>
    <div class="promedios">{"".join(
        f'<div class="tile {color}"><div class="rotulo"><i></i>{rotulo}</div><b>{cifra}</b>'
        "</div>" for color, rotulo, cifra in promedios)}</div>
    <div class="chispa">{icono("chispa")}<span>El margen es de <b>{margen:.1f} %</b> y el
      <b>{parte_fiado:.1f} %</b> de lo vendido quedó a fiado.</span></div>
    <div class="actualizado"><i></i>Datos actualizados el {actualizado}</div>
  </div>
  <div class="card">
    <div class="card-cabeza"><span class="chip-icono">{icono("productos")}</span>
      <b>Productos con más ganancia</b><span class="pastilla">Top 5 del mes</span></div>
    <div class="top3">{filas_top}</div>
    <a class="ver" {ir("productos")}>Ver los 10 productos {icono("flecha", 2)}</a>
  </div>
</div>
""")

    # Accesos rápidos: cada uno abre su vista con solo esa información.
    bloque("accesos", "Accesos rápidos",
           '<span class="pastilla">Toca una tarjeta para entrar</span>')
    lider = nombre(top5.iloc[0]["producto"]) if len(top5) else "—"
    caros = (int((comparativo["diferencia_pct"] > 5).sum())
             if "diferencia_pct" in comparativo else 0)
    datos_acceso = {"venta": f"Mejor día del mes: {pesos(mes['venta'].max() if len(mes) else 0)}",
                    "productos": f"Líder: {lider}",
                    "precios": f"Más caro en {caros} productos",
                    "competencia": f"{len(tiendas)} tiendas en la zona",
                    "clima": f"{len(fiados)} clientes con fiado"}
    html('<div class="accesos">' + "".join(
        f'<a class="card acceso" {ir(c)}><span class="chip-icono">{icono(VISTAS[c][1])}</span>'
        f'<b>{VISTAS[c][2]}</b><p>{VISTAS[c][3]}</p><span class="dato">{dato}</span>'
        f'<span class="entrar">Entrar {icono("flecha", 2)}</span></a>'
        for c, dato in datos_acceso.items()) + "</div>")


# --- Vista: informe del mes -------------------------------------------------------------
# Cierre del mes contra el anterior (lo que la vista "Venta" no hace: esa muestra la historia
# larga). Todo se compara con los mismos días del mes anterior, salvo el cierre de ese mes.
elif vista == "informe":
    cabecera_vista("informe")
    nombre_ant = MESES[mes_ant.month - 1]
    mes_previo = diarias[diarias["fecha"].dt.to_period("M") == mes_ant]
    # El botón llama a window.print(); st.html deja correr ese script (st.markdown lo quitaría).
    st.html(f'<div class="acciones-informe"><span class="periodo">{icono("semana")}'
            f"<span><b>{periodo}</b> · comparado con {vs}</span></span>"
            f'<button type="button" class="imprimir" id="imprimir-informe">'
            f'{icono("imprimir", 1.8)}Imprimir o guardar en PDF</button></div>'
            "<script>document.getElementById('imprimir-informe')"
            ".addEventListener('click', () => window.print());</script>",
            unsafe_allow_javascript=True)

    if not len(mes) or not len(anterior):
        with st.container(border=True, key="tarjeta_informe_vacio"):
            vacio("informe", "Todavía no hay con qué comparar",
                  "El informe necesita ventas de este mes y del mes anterior.")
    else:
        # --- 1. Lo que hay que saber: 4 conclusiones escritas a partir de los datos ---------
        venta_act, venta_ant = mes["venta"].sum(), anterior["venta"].sum()
        mejor = mes.loc[mes["venta"].idxmax()]
        f = mejor["fecha"]
        evento = mejor["evento"] if isinstance(mejor["evento"], str) else ""
        contexto = (f", día de {EVENTOS.get(evento, evento).lower()}" if evento else
                    ", día de quincena" if f.day in (1, 15, 16, 30, 31) else
                    ", en fin de semana" if f.weekday() >= 5 else "")
        hallazgos = [("h-neutro", "semana",
                      f"Tu mejor día fue el <b>{DIAS_LARGOS[f.weekday()]} {f.day}</b>{contexto}, "
                      f"con <b>{pesos(mejor['venta'])}</b>.")]
        finde = mes["fecha"].dt.day_of_week >= 5
        if finde.any() and (~finde).any():
            extra = (mes.loc[finde, "venta"].mean() / mes.loc[~finde, "venta"].mean() - 1) * 100
            hallazgos.append(("h-neutro", "barras",
                              f"Sábado y domingo vendieron <b>{abs(extra):.0f} % "
                              f"{'más' if extra >= 0 else 'menos'}</b> por día que entre semana."))
        fiado_act, fiado_ant = mes["venta_fiado"].sum(), anterior["venta_fiado"].sum()
        if fiado_ant:
            cambio_fiado = (fiado_act / fiado_ant - 1) * 100
            hallazgos.append(("h-mal" if cambio_fiado > 0 else "h-bien", "fiado",
                              f"El fiado {'subió' if cambio_fiado > 0 else 'bajó'} "
                              f"<b>{abs(cambio_fiado):.1f} %</b> contra {vs}; es el "
                              f"<b>{fiado_act / venta_act * 100:.1f} %</b> de la venta."))
        margen_act = mes["ganancia"].sum() / venta_act * 100
        margen_ant = anterior["ganancia"].sum() / venta_ant * 100
        hallazgos.append(("h-bien" if margen_act >= margen_ant else "h-mal", "ganancia",
                          f"El margen fue de <b>{margen_act:.1f} %</b> (en {nombre_ant}, "
                          f"{margen_ant:.1f} %) y cada ticket dejó en promedio "
                          f"<b>{pesos(venta_act / mes['tickets'].sum())}</b>."))
        # &nbsp; para que "37 %" no se parta en dos renglones.
        html(f'<div class="card saber"><div class="card-cabeza"><span class="chip-icono">'
             f'{icono("chispa")}</span><b>Lo que hay que saber</b></div>'
             '<div class="hallazgos">' + "".join(
                 f'<div class="hallazgo {tono}"><span class="h-icono">{icono(dibujo)}</span>'
                 f'<p>{texto.replace(" %", "&nbsp;%")}</p></div>'
                 for tono, dibujo, texto in hallazgos) + "</div></div>")

        # --- 2. Carrera contra el mes anterior: venta acumulada día por día ----------------
        with st.container(border=True, key="tarjeta_carrera"):
            def acumulada(tabla):
                t = tabla.sort_values("fecha")
                return pd.Series(t["venta"].cumsum().to_numpy(), index=t["fecha"].dt.day)

            carrera = (pd.DataFrame({"ahora": acumulada(mes), "antes": acumulada(mes_previo)})
                       .rename_axis("dia").reset_index())
            for col in ("ahora", "antes"):
                carrera[f"{col}_txt"] = carrera[col].map(
                    lambda v: "—" if pd.isna(v) else pesos(v))
            mes_corto = nombre_mes.split()[0].capitalize()
            titulo_tarjeta("serie", f"Carrera contra {nombre_ant}",
                           f"Venta sumada día por día {punto(AZUL)}{mes_corto}"
                           f'<span class="raya"></span>{nombre_ant.capitalize()}',
                           (carrera[["dia", "ahora", "antes"]], "carrera_del_mes.csv"))
            dia_hoy = int(mes["fecha"].dt.day.max())
            proyeccion = venta_act / mes["fecha"].nunique() * ultimo_mes.days_in_month
            minis = [(f"Llevas al día {dia_hoy}", pesos(venta_act)),
                     (f"{nombre_ant.capitalize()} al día {dia_hoy}", pesos(venta_ant)),
                     ("Cierre estimado del mes", pesos(proyeccion))]
            html('<div class="minis">' + "".join(
                f'<div class="mini"><span>{etiqueta}</span><b>{valor}</b></div>'
                for etiqueta, valor in minis) + "</div>")

            dias_eje = alt.Axis(values=[1, 8, 15, 22, 29], labelExpr="'Día ' + datum.value")
            eje_x = alt.X("dia:Q", title=None, scale=alt.Scale(domain=[1, 31], nice=False),
                          axis=dias_eje)
            eje_y = alt.Axis(format="$,.0f")
            ahora = alt.Chart(carrera.dropna(subset=["ahora"])).encode(
                x=eje_x, y=alt.Y("ahora:Q", title=None, axis=eje_y))
            antes = alt.Chart(carrera.dropna(subset=["antes"])).encode(
                x=eje_x, y=alt.Y("antes:Q", title=None, axis=eje_y))
            area = ahora.mark_area(color=degradado("rgba(37,99,235,0)", "rgba(37,99,235,0.16)",
                                                   vertical=True))
            linea_antes = antes.mark_line(color=TEXTO_EJE, strokeDash=[6, 4], strokeWidth=2)
            linea_ahora = ahora.mark_line(color=AZUL, strokeWidth=3)
            # Dónde va cada mes el último día con datos, y en cuánto cerró el mes anterior.
            hoy_fila = carrera[carrera["dia"] == dia_hoy]
            punta = alt.Chart(hoy_fila).encode(x=eje_x, y="ahora:Q")
            punta = (punta.mark_circle(size=90, color=AZUL, stroke="white", strokeWidth=2,
                                       opacity=1)
                     + punta.mark_text(dy=-16, fontSize=12, fontWeight=800, color=AZUL,
                                       text=pesos(venta_act)))
            par = alt.Chart(hoy_fila).mark_circle(size=60, color=TEXTO_EJE, stroke="white",
                                                  strokeWidth=2, opacity=1).encode(
                x=eje_x, y="antes:Q")
            cierre = alt.Chart(carrera.dropna(subset=["antes"]).tail(1)).encode(
                x=eje_x, y="antes:Q")
            cierre = (cierre.mark_circle(size=50, color=TEXTO_EJE, opacity=1)
                      + cierre.mark_text(align="right", dx=-8, dy=-12, fontSize=11,
                                         fontWeight=700, color=TEXTO_EJE,
                                         text=f"Cerró en {pesos(mes_previo['venta'].sum())}"))
            # Al pasar el cursor: línea vertical y un globo con los dos meses de ese día.
            cursor = alt.selection_point(nearest=True, on="pointerover", clear="pointerout",
                                         fields=["dia"], empty=False)
            selector = alt.Chart(carrera).mark_point(opacity=0).encode(
                x=eje_x, y="antes:Q",
                tooltip=[alt.Tooltip("dia:Q", title="Día"),
                         alt.Tooltip("ahora_txt:N", title=mes_corto),
                         alt.Tooltip("antes_txt:N", title=nombre_ant.capitalize())]
            ).add_params(cursor)
            guia = alt.Chart(carrera).mark_rule(color=TEXTO_EJE, strokeDash=[4, 3]).encode(
                x=eje_x).transform_filter(cursor)
            st.altair_chart(estilo(alt.layer(area, linea_antes, linea_ahora, guia, cierre, par,
                                             punta, selector), ALTO_SERIE))
            diferencia = (venta_act / venta_ant - 1) * 100
            lectura(f"Vas <b>{abs(diferencia):.1f} % {'arriba' if diferencia >= 0 else 'abajo'}"
                    f"</b> de {nombre_ant} a la misma fecha; a este ritmo cerrarías "
                    f"{nombre_mes.split()[0]} en unos <b>{pesos(proyeccion)}</b>")

        # --- 3. Qué cambió: productos que suben y que bajan (venta por día) ----------------
        # Se compara la venta POR DÍA de cada producto: el mes en curso puede ir a la mitad.
        def por_dia(periodo_mes, tabla):
            filas = producto[producto["mes"] == str(periodo_mes)].set_index("producto")
            return filas["venta"] / max(tabla["fecha"].nunique(), 1)

        cambio = pd.DataFrame({"ahora": por_dia(ultimo_mes, mes),
                               "antes": por_dia(mes_ant, mes_previo)}).dropna()
        cambio["pct"] = (cambio["ahora"] / cambio["antes"] - 1) * 100
        listas = [("Productos que suben", "sube", "h-bien", "bien",
                   cambio[cambio["pct"] > 0].nlargest(5, "pct"),
                   "Ningún producto vendió más que el mes pasado."),
                  ("Productos que bajan", "baja", "h-mal", "mal",
                   cambio[cambio["pct"] < 0].nsmallest(5, "pct"),
                   "Ningún producto vendió menos que el mes pasado.")]
        tarjetas_cambio = []
        for titulo, flecha, tono, clase, tabla, vacia in listas:
            filas = "".join(
                f'<div class="fila-cambio {tono}">{ficha(clave)}'
                f'<span class="nom">{nombre(clave)}</span><span class="por-dia">'
                f'{pesos(p["ahora"])} por día</span><span class="cambio {clase}">'
                f'{icono(flecha, 2.2)}{abs(p["pct"]):.1f} %</span></div>'
                for clave, p in tabla.iterrows())
            tarjetas_cambio.append(
                f'<div class="card"><div class="card-cabeza"><span class="chip-icono">'
                f'{icono(flecha)}</span><b>{titulo}</b><span class="pastilla">Venta por día vs '
                f'{nombre_ant}</span></div>'
                + (f'<div class="cambios">{filas}</div>' if filas else
                   f'<p class="sin-cambios">{vacia}</p>') + "</div>")
        html(f'<div class="duo">{"".join(tarjetas_cambio)}</div>')
    pasos("informe")

# --- Vista: venta por día ------------------------------------------------------------
elif vista == "venta":
    cabecera_vista("venta")
    with st.container(border=True, key="tarjeta_venta_dia"):
        # El promedio se calcula con toda la historia y después se recorta al rango elegido.
        serie = diarias[["fecha", "venta"]].assign(
            promedio=diarias["venta"].rolling(7, min_periods=1).mean())
        titulo_tarjeta("serie", "Venta por día", f"{punto(AZUL_CLARO)}Venta de cada día "
                       f"{punto(AZUL)}Promedio de 7 días", (serie.round(2), "venta_por_dia.csv"))
        rangos = {"3 meses": 3, "6 meses": 6, "12 meses": 12, "Todo": None}
        rango = st.segmented_control("Periodo", list(rangos), default="12 meses",
                                     key="rango_venta", label_visibility="collapsed") or "Todo"
        if rangos[rango]:
            desde = serie["fecha"].max() - pd.DateOffset(months=rangos[rango])
            serie = serie[serie["fecha"] > desde]
        meses_corto = str([m[:3] for m in MESES])
        eje_fecha = alt.Axis(tickCount="month", labelExpr=(
            f"{meses_corto}[month(datum.value)] + ' ' + timeFormat(datum.value, '%y')"))
        base = alt.Chart(serie).encode(x=alt.X("fecha:T", title=None, axis=eje_fecha))
        area = base.mark_area(color=degradado("rgba(37,99,235,0)", "rgba(37,99,235,0.14)",
                                              vertical=True)).encode(y="venta:Q")
        diaria = base.mark_line(color=AZUL_CLARO, strokeWidth=1.2).encode(
            y=alt.Y("venta:Q", title=None, axis=alt.Axis(format="$,.0f")))
        semanal = base.mark_line(color=AZUL, strokeWidth=2.6).encode(y="promedio:Q")
        # Guía al pasar el cursor: el día más cercano muestra una línea vertical, un punto en cada
        # serie y un solo globo con la venta y el promedio de ese día.
        cursor = alt.selection_point(nearest=True, on="pointerover", clear="pointerout",
                                     fields=["fecha"], empty=False)
        selector = base.mark_point(opacity=0).encode(
            y="venta:Q", tooltip=[alt.Tooltip("fecha:T", title="Fecha", format="%d/%m/%Y"),
                                  dinero("venta", "Venta"), dinero("promedio", "Promedio 7 días")]
        ).add_params(cursor)
        guia = base.mark_rule(color=TEXTO_EJE, strokeDash=[4, 3]).transform_filter(cursor)
        marcas = [base.mark_circle(size=64, color=c, stroke="white", strokeWidth=2)
                  .encode(y=f"{campo}:Q").transform_filter(cursor)
                  for campo, c in (("venta", AZUL_MEDIO), ("promedio", AZUL))]
        # El mejor día del rango queda marcado en la gráfica (lo explica la lectura de abajo).
        mejor = serie.loc[serie["venta"].idxmax()]
        pico = alt.Chart(serie.loc[[mejor.name]]).encode(x="fecha:T", y="venta:Q")
        pico = (pico.mark_circle(size=80, color=AMBAR, stroke="white", strokeWidth=2, opacity=1)
                + pico.mark_text(align="left", dx=9, fontSize=12, fontWeight=700, color=AMBAR_TEXTO,
                                 text="Mejor día"))
        st.altair_chart(estilo(alt.layer(area, diaria, semanal, guia, *marcas, pico, selector),
                               ALTO_SERIE))
        lectura(f"Mejor día del periodo: <b>{DIAS_LARGOS[mejor['fecha'].weekday()]} "
                f"{mejor['fecha'].day} de {MESES[mejor['fecha'].month - 1]} de "
                f"{mejor['fecha'].year}</b>, con <b>{pesos(mejor['venta'])}</b>")
    pasos("venta")

# --- Vista: productos y días fuertes -------------------------------------------------
elif vista == "productos":
    cabecera_vista("productos")
    col_prod, col_dia, col_evento = st.columns(3, gap="medium")
    with col_prod, st.container(border=True, key="tarjeta_productos"):
        top = producto[producto["mes"] == str(ultimo_mes)].nlargest(10, "ganancia")
        titulo_tarjeta("productos", "Productos con más ganancia",
                       f"Top 10 por ganancia en {MESES[ultimo_mes.month - 1]} "
                       f"{punto(*ESCALA_AZUL)}Menor a mayor", (top, "productos_top10.csv"))
        st.altair_chart(estilo(barras_horizontales(
            con_fichas(top), "ganancia", "producto",
            [alt.Tooltip("producto:N", title="Producto"), dinero("ganancia", "Ganancia"),
             alt.Tooltip("piezas:Q", title="Piezas", format=",")],
            alt.Color("ganancia:Q", legend=None, scale=alt.Scale(range=ESCALA_AZUL)),
            fichas=True), ALTO_FILA))
        if len(top):
            lider = top.iloc[0]
            lectura(f"<b>{nombre(lider['producto'])}</b> deja el "
                    f"<b>{lider['ganancia'] / top['ganancia'].sum() * 100:.0f} %</b> "
                    "de la ganancia del top 10")

    with col_dia, st.container(border=True, key="tarjeta_dias"):
        # Índice 0-6 = lunes-domingo (sirve para DIAS_LARGOS).
        por_dia = (diarias.groupby("dia_semana")["venta"].mean().reindex(list(DIAS))
                   .rename(index=DIAS).rename_axis("dia").reset_index())
        titulo_tarjeta("semana", "Venta por día de la semana",
                       f"Promedio diario {punto(*VERDE_FUERTE)}El más fuerte "
                       f"{punto(*AZUL_SUAVE)}Los demás",
                       (por_dia.round(2), "venta_por_dia_semana.csv"))
        fuerte = por_dia.loc[por_dia["venta"].idxmax()]
        sel, opacidad = resalte("dia")
        barras = alt.Chart(por_dia).mark_bar(cornerRadiusEnd=6).encode(
            x=alt.X("dia:N", sort=list(DIAS.values()), title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("venta:Q", title=None, axis=alt.Axis(format="$,.0f")),
            color=alt.condition(alt.datum.venta == fuerte["venta"],
                                alt.value(degradado(*VERDE_FUERTE, vertical=True)),
                                alt.value(degradado(*AZUL_SUAVE, vertical=True))),
            opacity=opacidad,
            tooltip=[alt.Tooltip("dia:N", title="Día"), dinero("venta", "Venta promedio")])
        st.altair_chart(estilo(barras.add_params(sel), ALTO_FILA))
        extra = (fuerte["venta"] / por_dia["venta"].iloc[:5].mean() - 1) * 100
        lectura(f"El <b>{DIAS_LARGOS[fuerte.name]}</b> vende <b>{extra:.0f} % más</b> que un día "
                "entre semana")

    with col_evento, st.container(border=True, key="tarjeta_eventos"):
        eventos = (diarias.assign(evento=diarias["evento"].fillna("").replace("", "normal"))
                   .groupby("evento")["venta"].agg(promedio="mean", dias="count").reset_index())
        eventos["nombre"] = eventos["evento"].map(EVENTOS).fillna(eventos["evento"])
        titulo_tarjeta("eventos", "Eventos vs días normales",
                       f"Venta promedio por día {punto(*VERDE_FUERTE)}Con evento "
                       f"{punto(*VERDE_SUAVE)}Normal",
                       (eventos[["nombre", "promedio", "dias"]].round(2), "venta_eventos.csv"))
        st.altair_chart(estilo(barras_horizontales(
            eventos, "promedio", "nombre",
            [alt.Tooltip("nombre:N", title="Tipo de día"), dinero("promedio", "Venta promedio"),
             alt.Tooltip("dias:Q", title="Días")],
            alt.condition(alt.datum.evento == "normal", alt.value(degradado(*VERDE_SUAVE)),
                          alt.value(degradado(*VERDE_FUERTE)))), ALTO_FILA))
        normal = eventos.loc[eventos["evento"] == "normal", "promedio"]
        especiales = eventos[eventos["evento"] != "normal"]
        if len(normal) and len(especiales):
            pico = especiales.loc[especiales["promedio"].idxmax()]
            lectura(f"La <b>{pico['nombre'].lower()}</b> vende "
                    f"<b>{pico['promedio'] / normal.iloc[0]:.1f} veces</b> lo de un día normal")
    pasos("productos")

# --- Vista: precios del mercado (PROFECO) ---------------------------------------------
# Sale de data/oro/comparativo_precios.csv y precios_por_cadena.csv (pipeline/precios.py).
elif vista == "precios":
    cabecera_vista("precios")
    con = (comparativo.dropna(subset=["mercado_mediana"])
           if "mercado_mediana" in comparativo else pd.DataFrame())
    if not len(con):
        with st.container(border=True, key="tarjeta_precios_vacio"):
            vacio("precios", "Todavía no hay precios del mercado",
                  "Corre <code>python -m extractores.precios_profeco</code> y luego "
                  "<code>python -m pipeline.ejecutar</code> para traer los precios de PROFECO.")
    else:
        zona = con["zona"].iloc[0]
        fecha = pd.to_datetime(con["fecha_precios"]).max()
        mes_precios = f"{MESES[fecha.month - 1]} de {fecha.year}"
        cerca = "" if zona.startswith("Colima") else (
            "PROFECO no registra precios en Colima, así que se usan los de la "
            f"<b>{zona.lower()}</b>, la más cercana con datos. ")
        html(f'<div class="aviso"><span class="insignia">Referencia</span><span>{cerca}Precios '
             f"de {mes_precios} en supermercados, tiendas de conveniencia, mercados y "
             "tortillerías (PROFECO, Quién es Quién en los Precios). Cada precio se lleva a la "
             "misma cantidad que vendes tú.</span></div>")
        caros = con[con["diferencia_pct"] > 5]
        conviene = con[con["ahorro_por_pieza"] > 0]
        minis = [("Productos comparados", f"{len(con)} de {len(comparativo)}"),
                 ("Más caros que el mercado", f"{len(caros)}"),
                 ("Ahorro posible al mes", pesos(con["ahorro_mes"].sum()))]
        html('<div class="minis minis-precios">' + "".join(
            f'<div class="mini"><span>{etiqueta}</span><b>{valor}</b></div>'
            for etiqueta, valor in minis) + "</div>")

        def centavos(x):
            return f"${x:,.2f}"

        def marca(m):
            return "Sin marca (granel)" if m == "S/M" else m

        # --- Buscador: encuentra un producto aunque se escriba con errores (tablero/buscador.py).
        # Cada producto se busca por su nombre, sinónimos, descripción, categoría y las marcas
        # que PROFECO registra para él. Las fichas de "También" llevan ?q= para buscarlas.
        mercado = leer(PLATA / "precios_mercado.csv")
        marcas = (mercado.groupby("producto_tienda")["marca"].unique() if len(mercado)
                  else pd.Series(dtype=object))
        docs = [documento(r["producto"], nombre(r["producto"]),
                          r["equivalente"] if isinstance(r["equivalente"], str) else "",
                          r["categoria"], marcas.get(r["producto"], ()))
                for _, r in comparativo.iterrows()]
        encontrados = []
        with st.container(border=True, key="tarjeta_buscador"):
            titulo_tarjeta("buscar", "Busca un producto",
                           "Escribe como quieras y presiona Enter: entiende errores de dedo, "
                           "nombres comunes (chesco, papel de baño) y marcas (Lala, Bimbo)")
            consulta = st.text_input("Buscar un producto", key="buscar_precio",
                                     value=st.query_params.get("q", ""),
                                     placeholder="Ej.: asucar, chesco, jabon, lala…",
                                     label_visibility="collapsed")
            if consulta.strip():
                encontrados = buscar(consulta, docs)
            if consulta.strip() and not encontrados:
                html(f'<p class="sin-resultados">No encontramos «{consulta.strip()}». Prueba '
                     "con otra palabra: azúcar, refresco, leche, detergente…</p>")
            elif encontrados:
                clave = encontrados[0][0]
                r = comparativo.set_index("producto").loc[clave]
                doc = next(d for d in docs if d["clave"] == clave)
                quisiste = (f'<span class="quisiste">¿Quisiste decir <b>{nombre(clave)}</b>?'
                            "</span>" if hubo_correccion(consulta, doc) else "")
                cuantos = (f"{len(encontrados)} resultados" if len(encontrados) > 1
                           else "1 resultado")
                que_es = (r["equivalente"] if isinstance(r["equivalente"], str)
                          else r["categoria"])
                partes = [f'<div class="resultado-cabeza">{ficha(clave, tam="grande")}<div>'
                          f'<b>{nombre(clave)}</b><small>{que_es}</small>{quisiste}</div>'
                          f'<span class="pastilla">{cuantos}</span></div>']
                if pd.notna(r["mercado_mediana"]):
                    dif = r["diferencia_pct"]
                    tono = "mal" if dif > 5 else "bien" if dif < -5 else "neutro"
                    propia = (f'<b>{centavos(r["mercado_min"])}</b><small>{r["mejor_marca"]} · '
                              f'{r["mejor_cadena"]}</small>' if r["mejor_marca_propia"] else
                              "<b>—</b><small>No hay más barata</small>")
                    fichas_dato = [
                        ("Tu precio", f'<b>{centavos(r["tu_precio"])}</b><small>'
                                      f'<span class="cambio {tono}">{dif:+.1f} %</span> contra '
                                      "el mercado</small>"),
                        ("Mediana del mercado", f'<b>{centavos(r["mercado_mediana"])}</b>'
                                                f'<small>En {int(r["tiendas"])} tiendas</small>'),
                        ("Marca comercial más barata",
                         f'<b>{centavos(r["comercial_precio"])}</b><small>'
                         f'{marca(r["comercial_marca"])} · {r["comercial_tienda"]}</small>'),
                        ("Marca propia más barata", propia)]
                    partes.append('<div class="minis cuatro">' + "".join(
                        f'<div class="mini"><span>{e}</span>{v}</div>'
                        for e, v in fichas_dato) + "</div>")
                    lugar = ("en línea con el mercado" if tono == "neutro" else
                             f"<b>{abs(dif):.0f} % {'arriba' if dif > 0 else 'abajo'}</b> del "
                             "mercado")
                    cual = ("a granel" if r["comercial_marca"] == "S/M"
                            else r["comercial_marca"])
                    surtir = (f"; si surtes {cual} en "
                              f"{r['comercial_tienda']}, tu costo baja "
                              f"<b>{centavos(r['ahorro_por_pieza'])}</b> por pieza (unos "
                              f"<b>{pesos(r['ahorro_mes'])}</b> al mes)"
                              if r["ahorro_por_pieza"] > 0 else
                              "; tu costo ya es menor que la marca comercial más barata")
                else:
                    partes.append('<p class="sin-resultados">PROFECO no registra un producto '
                                  "equivalente, así que no se puede comparar su precio.</p>")
                    lugar = surtir = ""
                otros = "".join(
                    f'<a class="otro" href="?vista=precios&amp;q={quote(nombre(c))}" '
                    f'target="_self">{ficha(c)}{nombre(c)}</a>' for c, _ in encontrados[1:])
                if otros:
                    partes.append(f'<div class="otros"><span>También:</span>{otros}</div>')
                html('<div class="resultado">' + "".join(partes) + "</div>")
                if lugar:
                    lectura(f"Tu precio está {lugar}{surtir}")

        col_tu, col_cadena = st.columns(2, gap="medium")
        cad = (cadenas[cadenas["productos"] >= 8].assign(diferencia=cadenas["indice"] - 100)
               if len(cadenas) else pd.DataFrame())
        alto = max(len(con), len(cad), 8) * 24 + 10

        def divergente(datos, campo, eje, tooltip, tolerancia, fichas=False):
            """Barras desde el cero: a la izquierda más barato (verde), a la derecha más caro
            (rojo) y en gris lo que está a menos de `tolerancia` % del mercado."""
            datos = datos.assign(
                tono=np.select([datos[campo] > tolerancia, datos[campo] < -tolerancia],
                               ["caro", "barato"], "parecido"),
                txt=datos[campo].map(lambda v: f"{v:+.1f} %"))
            orden = list(datos.sort_values(campo, ascending=False)[eje])
            con_signo = "(datum.value > 0 ? '+' : '') + datum.value + ' %'"
            eje_y = alt.Y(f"{eje}:N", sort=orden, title=None,
                          axis=alt.Axis(labelPadding=32) if fichas else alt.Undefined)
            base = alt.Chart(datos).encode(
                y=eje_y,
                x=alt.X(f"{campo}:Q", title=None, scale=alt.Scale(nice=True, padding=40),
                        axis=alt.Axis(labelExpr=con_signo)),
                tooltip=tooltip)
            sel, opacidad = resalte(eje)
            barras = base.mark_bar(cornerRadiusEnd=4).encode(
                opacity=opacidad,
                color=alt.Color("tono:N", legend=None, scale=alt.Scale(
                    domain=["caro", "barato", "parecido"], range=[ROJO, VERDE, GRIS])))
            cero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=TEXTO_EJE).encode(x="x:Q")
            textos = [base.transform_filter(f"datum.{campo} {signo} 0").mark_text(
                align=lado, dx=dx, fontSize=11, fontWeight=700, color=TEXTO).encode(text="txt:N")
                for signo, lado, dx in ((">=", "left", 5), ("<", "right", -5))]
            capas = barras.add_params(sel) + cero + textos[0] + textos[1]
            return capas + fichas_en_eje(datos, eje_y) if fichas else capas

        with col_tu, st.container(border=True, key="tarjeta_tu_precio"):
            titulo_tarjeta("precios", "Tu precio contra el mercado",
                           f"Contra la mediana de PROFECO {punto(ROJO)}Más caro "
                           f"{punto(VERDE)}Más barato {punto(GRIS)}Parecido (±5 %)",
                           (con[["producto", "tu_precio", "mercado_mediana", "mercado_min",
                                 "tiendas", "diferencia_pct"]], "tu_precio_vs_mercado.csv"))
            st.altair_chart(estilo(divergente(
                con_fichas(con), "diferencia_pct", "producto",
                [alt.Tooltip("producto:N", title="Producto"), dinero("tu_precio", "Tu precio"),
                 dinero("mercado_mediana", "Mediana del mercado"),
                 alt.Tooltip("txt:N", title="Diferencia"),
                 alt.Tooltip("tiendas:Q", title="Tiendas comparadas")], 5, fichas=True),
                alto))
            if len(caros):
                peor = caros.loc[caros["diferencia_pct"].idxmax()]
                lectura(f"Estás arriba del mercado en <b>{len(caros)} productos</b>; el que más: "
                        f"<b>{nombre(peor['producto']).lower()}</b>, "
                        f"{peor['diferencia_pct']:+.0f} %")
            else:
                lectura("Tus precios están en línea con el mercado")

        with col_cadena, st.container(border=True, key="tarjeta_cadenas"):
            titulo_tarjeta("tienda", "¿Dónde conviene surtir?",
                           f"Precio promedio de cada cadena contra el mercado "
                           f"{punto(VERDE)}Más barata {punto(ROJO)}Más cara",
                           (cad, "precios_por_cadena.csv") if len(cad) else None)
            if len(cad):
                st.altair_chart(estilo(divergente(
                    cad, "diferencia", "cadena_comercial",
                    [alt.Tooltip("cadena_comercial:N", title="Cadena"),
                     alt.Tooltip("txt:N", title="Contra el mercado"),
                     alt.Tooltip("productos:Q", title="Productos comparados"),
                     alt.Tooltip("mas_barata_en:Q", title="Más barata en")], 2), alto))
                top = cad.iloc[0]
                lectura(f"<b>{top['cadena_comercial']}</b> sale <b>{-top['diferencia']:.1f} % más "
                        f"barata</b> que el mercado en {top['productos']} productos")
            else:
                vacio("tienda", "Pocas cadenas para comparar",
                      "Hace falta que una cadena tenga al menos 8 productos comparables.")

        # Tabla: la mejor alternativa por producto (las que convienen primero).
        with st.container(border=True, key="tarjeta_alternativas"):
            columnas = ["producto", "equivalente", "tu_costo", "comercial_marca",
                        "comercial_cadena", "comercial_tienda", "comercial_precio",
                        "ahorro_por_pieza", "ahorro_mes", "mejor_marca", "mejor_cadena",
                        "mercado_min", "mejor_marca_propia"]
            titulo_tarjeta("productos", "Mejor alternativa por producto",
                           "La opción más barata de marca comercial contra tu costo; aparte, la "
                           "marca propia de la cadena si sale más barata",
                           (con[columnas], "mejor_alternativa.csv"))
            tabla = con.sort_values(["ahorro_mes", "ahorro_por_pieza"], ascending=False)
            # Con una búsqueda, la tabla muestra solo lo encontrado (en orden de parecido).
            orden = [c for c, _ in encontrados if c in set(con["producto"])]
            if orden:
                tabla = con.set_index("producto").loc[orden].reset_index()
                html(f'<p class="filtrada">Mostrando {len(orden)} de {len(con)} productos por '
                     f"tu búsqueda «{consulta.strip()}». Borra el texto para ver todos.</p>")

            renglones = []
            for _, r in tabla.iterrows():
                ahorra = r["ahorro_por_pieza"] > 0
                propia = (f'<span class="propia">{r["mejor_marca"]} · {r["mejor_cadena"]}: '
                          f'<b>{centavos(r["mercado_min"])}</b></span>'
                          if r["mejor_marca_propia"] else '<span class="nada">—</span>')
                renglones.append(
                    f'<tr><td class="prod">{ficha(r["producto"])}<span><b>'
                    f'{nombre(r["producto"])}</b><small>{r["equivalente"]}</small></span></td>'
                    f'<td class="num" data-etiqueta="Tu costo">{centavos(r["tu_costo"])}</td>'
                    f'<td data-etiqueta="Marca comercial más barata">'
                    f'<b>{marca(r["comercial_marca"])}</b>'
                    f'<small>{r["comercial_tienda"]}</small></td>'
                    f'<td class="num" data-etiqueta="Precio">{centavos(r["comercial_precio"])}'
                    f'</td><td class="conviene" data-etiqueta="¿Conviene?">'
                    f'<span class="cambio {"bien" if ahorra else "neutro"}">'
                    + (f'Ahorras {centavos(r["ahorro_por_pieza"])}' if ahorra else
                       "Tu costo es menor")
                    + f'</span></td><td class="{"" if r["mejor_marca_propia"] else "sin-propia"}"'
                    f' data-etiqueta="Marca propia más barata">{propia}</td></tr>')
            html('<div class="tabla-envoltura"><table class="tabla-precios"><thead><tr>'
                 "<th>Producto</th><th>Tu costo</th><th>Marca comercial más barata</th>"
                 "<th>Precio</th><th>¿Conviene surtir ahí?</th><th>Marca propia más barata</th>"
                 f'</tr></thead><tbody>{"".join(renglones)}</tbody></table></div>')
            sin = comparativo[comparativo["mercado_mediana"].isna()]["producto"].map(nombre)
            lectura(f"Surtiendo esos <b>{len(conviene)} productos</b> con la opción más barata "
                    f"ahorrarías unos <b>{pesos(con['ahorro_mes'].sum())} al mes</b>, con lo "
                    "que vendiste en los últimos 30 días"
                    + (f". Sin equivalente en PROFECO: {', '.join(sin).lower()}" if len(sin)
                       else ""))
            st.caption("Fuente: PROFECO, Quién es Quién en los Precios (datos abiertos, "
                       "Términos de Libre Uso MX)."
                       + (" Los precios y costos de tu tienda son de demostración." if demo
                          else ""))
    pasos("precios")

# --- Vista: competencia en la zona --------------------------------------------------
elif vista == "competencia":
    cabecera_vista("competencia")
    with st.container(border=True, key="tarjeta_mapa"):
        if len(tiendas):
            aproximada = "" if TIENDA_PILOTO["coordenadas_confirmadas"] else (
                " · ubicación de la tienda piloto aproximada (centro de Villa de Álvarez)")
            titulo_tarjeta("mapa", "Tiendas alrededor de la tienda piloto",
                           f"{punto(AZUL)}Tienda piloto y círculo de {RADIO_COMPETENCIA_M} m "
                           f"{punto(VERDE)}Competencia directa {punto(GRIS)}Resto de la zona"
                           f"{aproximada}", (tiendas, "tiendas_zona.csv"))
            # La más cercana entre todas las tiendas de la zona (no solo las de menos de 500 m),
            # en línea recta con la fórmula del haversine.
            la0, lo0 = np.radians(TIENDA_PILOTO["lat"]), np.radians(TIENDA_PILOTO["lon"])
            la, lo = np.radians(tiendas["lat"]), np.radians(tiendas["lon"])
            h = np.sin((la - la0) / 2) ** 2 + np.cos(la0) * np.cos(la) * np.sin((lo - lo0) / 2) ** 2
            cercana = f"{(2 * 6_371_000 * np.arcsin(np.sqrt(h))).min():,.0f} m"
            minis = [(f"Tiendas a menos de {RADIO_COMPETENCIA_M} m", len(competencia)),
                     ("Tiendas en Colima y Villa de Álvarez", len(tiendas)),
                     ("La más cercana", cercana)]
            html('<div class="minis">' + "".join(
                f'<div class="mini"><span>{etiqueta}</span><b>{valor}</b></div>'
                for etiqueta, valor in minis) + "</div>")

            # Mapa centrado en la tienda piloto (st.map centra en el promedio de todas las tiendas).
            # Con el tema claro, map_style=None usa el mapa base claro de Streamlit.
            cerca = set(competencia["osm_id"]) if len(competencia) else set()
            puntos = tiendas[["osm_id", "nombre", "lat", "lon"]].assign(
                nombre=tiendas["nombre"].fillna("Tienda sin nombre"),
                rgb=[rgb(VERDE) if i in cerca else rgb(GRIS, 230) for i in tiendas["osm_id"]])
            piloto = pd.DataFrame({"nombre": [tienda], "lat": [TIENDA_PILOTO["lat"]],
                                   "lon": [TIENDA_PILOTO["lon"]]})
            blanco = rgb("#FFFFFF")
            capas = [
                pdk.Layer("ScatterplotLayer", piloto, get_position="[lon, lat]",
                          get_radius=RADIO_COMPETENCIA_M, get_fill_color=rgb(AZUL, 28),
                          get_line_color=rgb(AZUL, 220), stroked=True,
                          line_width_min_pixels=1.5),
                pdk.Layer("ScatterplotLayer", puntos, get_position="[lon, lat]", get_radius=18,
                          radius_min_pixels=5, get_fill_color="rgb", get_line_color=blanco,
                          stroked=True, line_width_min_pixels=1, pickable=True),
                pdk.Layer("ScatterplotLayer", piloto, get_position="[lon, lat]", get_radius=30,
                          radius_min_pixels=9, get_fill_color=rgb(AZUL), get_line_color=blanco,
                          stroked=True, line_width_min_pixels=2, pickable=True),
            ]
            vista = pdk.ViewState(latitude=TIENDA_PILOTO["lat"], longitude=TIENDA_PILOTO["lon"],
                                  zoom=14.2)
            st.pydeck_chart(pdk.Deck(layers=capas, initial_view_state=vista, map_style=None,
                                     tooltip={"text": "{nombre}", "style": {
                                         "fontFamily": FUENTE, "fontSize": "13px",
                                         "backgroundColor": "#FFFFFF", "color": TINTA,
                                         "border": "1px solid #E3EAF6", "borderRadius": "10px",
                                         "padding": "6px 10px",
                                         "boxShadow": "0 10px 24px -12px rgba(37,99,235,.45)"}}),
                            height=ALTO_MAPA)
            if len(competencia):
                st.dataframe(competencia[["nombre", "giro", "distancia_m"]]
                             .rename(columns={"nombre": "Tienda", "giro": "Giro",
                                              "distancia_m": "Distancia (m)"}),
                             hide_index=True, use_container_width=True, height=220)
            st.caption("Fuente: © colaboradores de OpenStreetMap (ODbL). "
                       "Unión espacial con GeoPandas (EPSG:6372).")
        else:
            titulo_tarjeta("mapa", "Tiendas alrededor de la tienda piloto")
            vacio("mapa", "Todavía no hay mapa de la zona",
                  "Corre <code>python -m extractores.tiendas_osm</code> y luego "
                  "<code>python -m pipeline.ejecutar</code> para traer las tiendas de "
                  "OpenStreetMap.")
    pasos("competencia")

# --- Vista: clima y crédito ---------------------------------------------------------
elif vista == "clima":
    cabecera_vista("clima")
    col_clima, col_fiado = st.columns(2, gap="medium")
    with col_clima, st.container(border=True, key="tarjeta_clima"):
        con_clima = diarias.dropna(subset=["temp_max_c"])
        tramos = list(TRAMOS_CALOR)
        calor = (con_clima.assign(tramo=pd.cut(con_clima["temp_max_c"], [-99, 29, 31, 33, 99],
                                               right=False, labels=tramos))
                 .groupby("tramo", observed=True)["venta"].agg(promedio="mean", dias="count")
                 .reset_index())
        titulo_tarjeta("clima", "Venta según el calor",
                       "Venta diaria promedio por temperatura máxima (Open-Meteo)"
                       '<span class="raya"></span>Promedio general',
                       (calor.round(2), "venta_por_temperatura.csv") if len(calor) else None)
        if len(calor):
            general = con_clima["venta"].mean()
            # Diferencia de cada tramo contra el promedio de todos los días, ya como texto.
            calor["contra"] = (calor["promedio"] / general - 1) * 100
            calor["contra_txt"] = calor["contra"].map(lambda v: f"{v:+.1f} %")
            base = alt.Chart(calor).encode(
                x=alt.X("tramo:N", sort=tramos, title=None, axis=alt.Axis(labelAngle=0),
                        scale=alt.Scale(paddingInner=0.4)),
                y=alt.Y("promedio:Q", title=None, axis=alt.Axis(format="$,.0f"),
                        scale=alt.Scale(domainMax=calor["promedio"].max() * 1.2)),
                tooltip=[alt.Tooltip("tramo:N", title="Temperatura máxima"),
                         dinero("promedio", "Venta promedio"),
                         alt.Tooltip("contra_txt:N", title="Contra el promedio"),
                         alt.Tooltip("dias:Q", title="Días")])
            esquinas = {"cornerRadiusTopLeft": 8, "cornerRadiusTopRight": 8}
            sel, opacidad = resalte("tramo")
            barras = base.mark_bar(**esquinas).encode(opacity=opacidad, color=alt.Color(
                "tramo:N", legend=None,
                scale=alt.Scale(domain=tramos, range=list(TRAMOS_CALOR.values()))))
            # Brillo blanco que se desvanece hacia arriba: cada barra va de su tono claro al pleno.
            # Es la capa de encima, así que es la que recibe el cursor.
            brillo = base.mark_bar(**esquinas, color=degradado(
                "rgba(255,255,255,0.45)", "rgba(255,255,255,0)", vertical=True)).add_params(sel)
            promedio = alt.Chart(pd.DataFrame({"general": [general]})).mark_rule(
                color=TEXTO_EJE, strokeDash=[5, 4], strokeWidth=1.3).encode(
                y="general:Q", tooltip=[dinero("general", "Promedio de todos los días")])
            contra = base.mark_text(baseline="bottom", dy=-24, fontSize=11, fontWeight=700).encode(
                text="contra_txt:N",
                color=alt.condition(alt.datum.contra >= 0, alt.value(VERDE), alt.value(ROJO)))
            st.altair_chart(estilo(barras + brillo + promedio + cifras(base, "promedio", True)
                                   + contra, ALTO_FILA))
            alto, bajo = (calor.loc[calor["promedio"].idxmax()],
                          calor.loc[calor["promedio"].idxmin()])
            lectura(f"Los días de <b>{alto['tramo'][0].lower()}{alto['tramo'][1:]}</b> venden "
                    f"<b>{(alto['promedio'] / bajo['promedio'] - 1) * 100:.1f} % más</b> que los "
                    f"de <b>{bajo['tramo'][0].lower()}{bajo['tramo'][1:]}</b>")
        else:
            vacio("clima", "Sin datos de clima por ahora",
                  "Cuando el extractor de Open-Meteo traiga temperaturas, aquí verás cómo cambia "
                  "la venta con el calor.")

    with col_fiado, st.container(border=True, key="tarjeta_fiado"):
        deudores = fiados.nlargest(8, "adeudo_bruto") if len(fiados) else fiados
        titulo_tarjeta("clientes", "Clientes con más fiado",
                       "Fiado acumulado desde 2025, sin descontar pagos · claves anónimas",
                       (deudores, "clientes_fiado.csv") if len(fiados) else None)
        if len(fiados):
            st.altair_chart(estilo(barras_horizontales(
                deudores, "adeudo_bruto", "cliente_fiado",
                [alt.Tooltip("cliente_fiado:N", title="Cliente"),
                 dinero("adeudo_bruto", "Fiado acumulado"),
                 alt.Tooltip("compras:Q", title="Compras a fiado", format=",")],
                alt.value(degradado(*ROSA))), ALTO_FILA))
            parte = deudores["adeudo_bruto"].sum() / fiados["adeudo_bruto"].sum() * 100
            suma = pesos(deudores["adeudo_bruto"].sum())
            lectura(f"Estos {len(deudores)} clientes suman <b>{suma}</b>, el "
                    f"<b>{parte:.0f} %</b> de todo el fiado")
        else:
            vacio("clientes", "Sin ventas a fiado",
                  "Cuando registres ventas a fiado, aquí aparecerán los clientes que más deben.")
    pasos("clima")

# --- Pie de página --------------------------------------------------------------------------
volver = ('<a class="arriba" href="#inicio">↑ Volver arriba</a>' if vista == "inicio" else
          f'<a class="arriba" {ir("inicio")}>← Volver al resumen</a>')
html(f'<div class="pie">{logo("TABLERO DEL DUEÑO")}'
     "<div>Fuentes: punto de venta (demostración)<i></i>Open-Meteo<i></i>"
     "© colaboradores de OpenStreetMap<i></i>PROFECO (Quién es Quién en los Precios)</div>"
     "<div>Linaje: cada cifra sale de data/oro y trae fuente, archivo de bronce y fecha de "
     f'captura.</div>{volver}</div>')
