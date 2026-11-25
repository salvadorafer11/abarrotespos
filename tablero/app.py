"""Tablero de AbarrotesPOS para el dueño de la tienda.  streamlit run tablero/app.py

Estilo "informe financiero": papel marfil con rayas diagonales de grafito, hojas blancas,
tinta azul marino y un solo acento de latón. Cabecera centrada en banda de tinta con
emblema (tiendita en sello de latón), nombre, ficha del informe e índice de secciones. Newsreader
(serif editorial) para títulos y cifras, Inter para el texto y las gráficas. Las gráficas son
casi monocromas; el color se reserva para lo que significa algo (días fuertes, calor,
fiado). Streamlit quita las etiquetas <script>, así que todo el diseño va en ESTILOS; el tema
base vive en .streamlit/config.toml.

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

# --- PALETA: tinta, pizarra y latón sobre papel -----------------------------------------------
TINTA = "#10243F"  # azul marino: textos y títulos
AZUL = "#2155D0"  # azul eléctrico: dato principal de las gráficas
PIZARRA = "#93B0E6"  # azul claro: dato secundario
ACERO = "#3A6FDB"  # azul medio: puntos del mapa
LATON = "#BE9654"  # único acento: mejor día, tienda piloto
LATON_TEXTO = "#7E5D22"  # latón legible como texto sobre blanco
VERDE = "#1D7658"  # verde bosque: competencia, cambios buenos
VINO = "#9C2F3E"  # vino: fiado, cambios malos
TEXTO = "#283244"
TEXTO_EJE = "#5D6779"
REJILLA = "rgba(16, 36, 63, 0.08)"
FUENTE = "Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
# Degradados sobrios: escala de ganancia (de niebla a tinta), días con evento / día más fuerte
# (verde bosque), días normales (salvia), demás días (pizarra clara) y fiado (vino).
ESCALA_TINTA = ["#BCD0F5", AZUL]
VERDE_FUERTE = ("#135640", "#1D7658", "#3F9B79")
VERDE_SUAVE = ("#A7D2BF", "#D3EADF")
PIZARRA_SUAVE = ("#CFDDF7", "#9DB8EC")
VINO_DEGRADADO = ("#E4B8BF", "#C06873", VINO)
# Escala de temperatura en tonos tierra: azul acero (fresco) -> arena -> ocre -> terracota.
TRAMOS_CALOR = {"Menos de 29 °C": "#5F87AE", "29 a 31 °C": "#D2B978",
                "31 a 33 °C": "#C98A3E", "Más de 33 °C": "#A3472F"}

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
# Secciones del tablero: (número romano, nombre corto para el índice del encabezado).
SECCIONES = [("I", "Resumen"), ("II", "Venta"), ("III", "Competencia"),
             ("IV", "Clima y crédito")]

# Iconos (Heroicons, MIT) para indicadores y tarjetas.
ICONOS = {
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
    # Descarga (cabecera de tarjetas) y estado vacío
    "descarga": "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 "
                "12 16.5m0 0L7.5 12m4.5 4.5V3",
    # Flechas de los chips de tendencia y bombilla de las lecturas
    "sube": "m4.5 19.5 15-15m0 0H8.25m11.25 0v11.25",
    "baja": "m4.5 4.5 15 15m0 0V8.25m0 11.25H8.25",
    "idea": "M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 "
            "7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-"
            ".983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18",
    # Emblema del encabezado: tiendita con toldo
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

# Newsreader (serif editorial con tamaño óptico: formal y muy legible en cifras grandes) +
# Inter (texto, etiquetas y gráficas: de las sans más legibles en pantalla).
FUENTES_URL = ("https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,"
               "400..700;1,6..72,400..600&family=Inter:wght@400..700&display=swap")



ESTILOS = """
<style>
@import url('__FUENTES__');
:root {
  --tinta: #10243F; --texto: #283244; --texto-suave: #475467; --texto-tenue: #5D6779;
  --papel: #E1E7F0; --hoja: #FFFFFF; --hoja-tenue: #FAF8F4;
  --linea: #E6E2D9; --linea-fuerte: #D5CEC0;
  --laton: #BE9654; --laton-t: #7E5D22; --laton-claro: #EBD5A6;
  --verde: #1D7658; --vino: #9C2F3E;
  --ficha: linear-gradient(160deg, #1838A8 0%, #2155D0 55%, #1A72CF 100%);
  /* Color de las rayas: gris grafito con un toque azul (armoniza con la tinta). Sobre la banda
     de tinta del encabezado se usa su versión plata, porque el grafito no se distinguiría. */
  --grafito: #263041; --plata: #AEB9CC;
  /* Azul de acción: solo para lo que se toca (opción elegida, enlaces, estados) */
  --azul: #2F5FD0; --riel: #EEF0F4;
  /* Azul eléctrico del encabezado y el pie (más claro que la tinta, con brillo cian) */
  --neon-azul: linear-gradient(160deg, #1838A8 0%, #2155D0 52%, #1A72CF 100%);
  --neon-luz: radial-gradient(60% 110% at 50% 0%, rgba(103, 232, 249, .28), transparent 65%);
  /* Rayas diagonales paralelas: finas cada 12 px y una marcada cada 72 px (ritmo de regla) */
  --rayas: repeating-linear-gradient(135deg, rgba(0, 0, 0, .55) 0 1px, transparent 1px 12px);
  --rayas-marcadas: repeating-linear-gradient(135deg, #000 0 1.6px, transparent 1.6px 72px);
  /* Sombra en capas (contacto + ambiente + caída): las hojas parecen apoyadas sobre la mesa */
  --sombra: 0 1px 1px rgba(16, 36, 63, .04), 0 4px 10px -4px rgba(16, 36, 63, .08),
            0 18px 40px -22px rgba(16, 36, 63, .32);
  --serif: Newsreader, 'Iowan Old Style', Georgia, serif;
  --fuente: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
  /* Marco de todos los elementos: su color y un halo muy tenue del mismo tono */
  --marco-luz: color-mix(in srgb, var(--marco) 22%, transparent);
}
/* Marco de color: un solo azul neón (eléctrico -> rey -> cielo -> cian) que es el
   mismo en todos los elementos a la vez, porque se anima una sola variable en la raíz. Cambia
   en pasos (10 por segundo) para no recalcular la página en cada cuadro. */
@property --marco { syntax: '<color>'; inherits: true; initial-value: #2155D0; }
:root { animation: marco 40s steps(80) infinite; }
@keyframes marco { 0%, 100% { --marco: #2155D0; } 25% { --marco: #1A72CF; }
  50% { --marco: #3B82F6; } 75% { --marco: #0EA5E9; } }

.stApp, .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"],
.stApp button { font-family: var(--fuente) !important; }
.encabezado h1, div.bloque .num, div.bloque .titulo,
div.tarjeta-titulo, .mini b, div.pie .marca, .indice a span {
  font-family: var(--serif) !important; font-optical-sizing: auto; }
/* Cifras de los indicadores en Inter: números de ancho fijo, más limpios para leer montos */
.kpi-valor, .kpi-indice { font-family: var(--fuente) !important; }
::selection { background: rgba(190, 150, 84, .25); color: var(--tinta); }
.stApp, .stApp * { scrollbar-width: thin; scrollbar-color: rgba(16, 36, 63, .22) transparent; }

/* Ambiente: gris azulado (la misma gama que los indicadores del resumen) con brillo neón: un
   resplandor cian que cae desde arriba, halos de azul eléctrico a los lados y una viñeta azul
   tinta en las orillas que da profundidad.
   Encima, rayas diagonales de gris grafito (como papel de seguridad): una capa fija de color
   que solo se ve a través de las rayas; otra máscara las aclara hacia el centro, donde está
   el contenido. Las tarjetas son opacas, así que las rayas solo asoman entre ellas. */
.stApp { color: var(--texto); background-color: var(--papel); isolation: isolate;
  background-image:
    radial-gradient(70% 45% at 50% -6%, rgba(103, 232, 249, .42), rgba(103, 232, 249, 0) 70%),
    radial-gradient(50% 60% at -5% 55%, rgba(59, 130, 246, .26), rgba(59, 130, 246, 0) 70%),
    radial-gradient(50% 60% at 105% 35%, rgba(56, 189, 248, .26), rgba(56, 189, 248, 0) 70%),
    radial-gradient(60% 45% at 70% 105%, rgba(37, 99, 235, .18), rgba(37, 99, 235, 0) 70%),
    radial-gradient(150% 110% at 50% 45%, rgba(16, 36, 63, 0) 55%, rgba(16, 36, 63, .12) 100%);
  background-attachment: fixed;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }
.stApp::before { content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background: var(--grafito); opacity: .17;
  -webkit-mask-image: radial-gradient(110% 85% at 50% 45%, rgba(0, 0, 0, .3) 25%, #000 85%),
                      var(--rayas), var(--rayas-marcadas);
  -webkit-mask-composite: source-in, source-over;
  mask-image: radial-gradient(110% 85% at 50% 45%, rgba(0, 0, 0, .3) 25%, #000 85%),
              var(--rayas), var(--rayas-marcadas);
  mask-composite: intersect, add; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMain"] { scroll-behavior: smooth; }
.block-container { max-width: 1760px; padding: 3.75rem 2rem 2.5rem; }

/* Saludo: fecha de hoy, saludo según la hora y, a la derecha, cuándo se actualizaron los
   datos (con un punto verde que late suave) */
.saludo { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between;
  gap: 1rem 2rem; margin: 0 .25rem 1.4rem; }
.saludo .fecha-hoy { display: flex; align-items: center; gap: .6rem; font-size: .85rem;
  font-weight: 600; color: var(--texto-suave); }
.saludo .fecha-hoy i { width: .35rem; height: .35rem; border-radius: 9999px;
  background: var(--azul); }
.saludo .fecha-hoy span { font-weight: 500; color: var(--azul); }
.saludo .hola { font-family: var(--serif) !important; font-size: 2.35rem; font-weight: 600;
  letter-spacing: -.015em; line-height: 1.15; color: var(--tinta); margin: .35rem 0 .2rem; }
.saludo .hola em { color: var(--azul); }
.saludo p { margin: 0; font-size: .98rem; color: var(--texto-tenue); }
.actualizado { display: inline-flex; align-items: center; gap: .55rem; font-size: .82rem;
  font-weight: 500; color: var(--texto-suave); background: var(--hoja);
  border: 1px solid var(--linea); border-radius: 9999px; padding: .42rem .95rem;
  box-shadow: var(--sombra); }
.actualizado .pulso { width: .5rem; height: .5rem; border-radius: 9999px;
  background: var(--verde); animation: pulso 2.4s ease-out infinite; }
@keyframes pulso { 0% { box-shadow: 0 0 0 0 rgba(29, 118, 88, .45); }
  80%, 100% { box-shadow: 0 0 0 .45rem rgba(29, 118, 88, 0); } }

/* Marco compartido, hojas blancas y entrada suave al cargar ("backwards" no fija nada al
   terminar, así el hover sigue funcionando) */
.encabezado, .aviso, .kpi, div[class*="st-key-tarjeta"] {
  border: 1.5px solid var(--marco) !important;
  box-shadow: var(--sombra), 0 0 18px -8px var(--marco-luz);
  animation: entrada .6s cubic-bezier(.22, 1, .36, 1) backwards; }
@keyframes entrada { from { opacity: 0; transform: translateY(8px); } }
.kpi:nth-child(2) { animation-delay: .06s; }
.kpi:nth-child(3) { animation-delay: .12s; }
.kpi:nth-child(4) { animation-delay: .18s; }

/* Encabezado centrado tipo cabecera de informe ejecutivo: emblema (tiendita dentro de un
   sello de doble anillo de latón), rótulo, nombre y lema; debajo una ficha con periodo,
   tienda y corte separados por filetes, y el índice. Fondo tinta con un reflejo de latón. */
.encabezado { position: relative; overflow: hidden; border-radius: 1rem;
  margin-bottom: 1.25rem; padding: 3.2rem 2.5rem 2.3rem; display: flex; flex-direction: column;
  align-items: center; text-align: center; gap: 2.1rem; color: #F2F6FD;
  background: var(--neon-luz), var(--neon-azul); }
/* Las mismas rayas en gris plata sobre la banda de tinta, casi invisibles detrás del texto y
   más presentes hacia las orillas */
.encabezado::after { content: ""; position: absolute; inset: 0; pointer-events: none;
  background: var(--plata); opacity: .22;
  -webkit-mask-image: radial-gradient(60% 75% at 50% 45%, rgba(0, 0, 0, .12) 30%, #000 95%),
                      var(--rayas), var(--rayas-marcadas);
  -webkit-mask-composite: source-in, source-over;
  mask-image: radial-gradient(60% 75% at 50% 45%, rgba(0, 0, 0, .12) 30%, #000 95%),
              var(--rayas), var(--rayas-marcadas);
  mask-composite: intersect, add; }
.encabezado > * { position: relative; z-index: 1; }
.encabezado::before { content: ""; position: absolute; top: 0; left: 2.5rem; right: 2.5rem;
  height: 2px; background: linear-gradient(90deg, transparent, var(--laton-claro), transparent); }
.identidad { display: flex; flex-direction: column; align-items: center; gap: 1.05rem; }
/* Emblema tipo sello: dos anillos finos de latón con el texto "ABARROTES POS · ..." entre
   ellos (SVG que sigue un círculo) y la tiendita al centro */
.emblema { position: relative; flex: none; width: 7.4rem; height: 7.4rem; border-radius: 9999px;
  display: grid; place-items: center; margin-bottom: .3rem; color: #EED9B0;
  background: radial-gradient(circle at 32% 28%, #3A78EE, #1838A8 72%);
  box-shadow: 0 0 0 1px rgba(235, 213, 166, .55), 0 14px 30px -14px rgba(0, 0, 0, .7); }
.emblema .anillo { position: absolute; inset: 0; width: 100%; height: 100%; }
.emblema .anillo circle { fill: none; stroke: rgba(235, 213, 166, .55); stroke-width: .8; }
.emblema .anillo text { font-family: var(--fuente); font-size: 8.6px; font-weight: 600;
  fill: #EBD5A6; }
.emblema .centro { position: relative; display: grid; place-items: center; }
.emblema .centro svg { width: 2.5rem; height: 2.5rem; }
.sobretitulo { font-size: .9rem; font-weight: 600; letter-spacing: .24em;
  text-transform: uppercase; color: var(--laton-claro); }
/* Streamlit envuelve el texto del h1 en un span y le agrega un enlace de ancla: el span se
   acomoda en fila (nombre + etiqueta POS) y el enlace se oculta */
.encabezado h1 > span[data-heading-text] { display: inline-flex; align-items: center;
  flex-wrap: wrap; gap: .2rem .8rem; }
.encabezado [data-testid="stHeaderActionElements"] { display: none; }
.encabezado h1 { font-size: 4.4rem; font-weight: 600; letter-spacing: -.02em; line-height: 1.05;
  margin: 0; padding: 0; color: #F6F2EA !important; }
.encabezado h1 .pos { font-family: var(--fuente) !important; font-size: 1.1rem;
  font-weight: 600; letter-spacing: .24em; line-height: 1; color: var(--laton-claro);
  border: 1px solid rgba(235, 213, 166, .6); border-radius: .3rem;
  padding: .4rem .3rem .4rem .55rem; }
.encabezado .lema { margin: 0; font-size: 1.35rem; color: #D6E0F3; text-wrap: balance; }
/* Ficha: datos del informe en fila, con su etiqueta en versalitas y filetes entre ellos */
.ficha { margin: 0; display: flex; flex-wrap: wrap; justify-content: center;
  padding: 1.7rem 0 0; border-top: 1px solid rgba(255, 255, 255, .10);
  width: min(1040px, 100%); }
.ficha > div { padding: .15rem 2.75rem; }
.ficha > div + div { border-left: 1px solid rgba(255, 255, 255, .14); }
.ficha dt { font-size: .8rem; font-weight: 600; letter-spacing: .2em;
  text-transform: uppercase; color: rgba(235, 213, 166, .85); }
.ficha dd { margin: .45rem 0 0; font-size: 1.22rem; font-weight: 500; color: #F2F4F8; }
/* Índice: enlaces a cada sección, en pastillas de contorno fino */
.indice { display: flex; flex-wrap: wrap; justify-content: center; gap: .75rem; }
.indice a { display: inline-flex; align-items: center; gap: .55rem; font-size: 1rem;
  font-weight: 500; padding: .45rem 1.15rem .45rem .95rem; border-radius: 9999px;
  color: #E3E7EE !important; text-decoration: none !important;
  border: 1px solid rgba(255, 255, 255, .16); background: rgba(255, 255, 255, .03);
  transition: background .2s ease, border-color .2s ease, color .2s ease; }
.indice a span { font-style: italic; font-size: 1.18rem; color: var(--laton-claro); }
.indice a:hover { color: #FFFFFF !important; border-color: rgba(235, 213, 166, .7);
  background: rgba(235, 213, 166, .10); }

/* Aviso: hoja blanca con insignia en versalitas */
.aviso { display: flex; align-items: center; gap: .9rem; background: var(--hoja);
  border-radius: 1rem; padding: .85rem 1.25rem; color: var(--texto-suave); font-size: .95rem;
  line-height: 1.55; margin-bottom: .4rem; }
.aviso code { color: var(--tinta); background: var(--hoja-tenue); }
.insignia { flex: none; font-size: .7rem; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; border-radius: .3rem; padding: .22rem .6rem;
  color: var(--laton-t); border: 1px solid rgba(190, 150, 84, .55); }

/* Secciones: numeral romano en cursiva de latón dentro de una ficha azul tinta, y título
   serif sobre un filete con un tramo grueso de latón al inicio */
div.bloque { display: flex; align-items: center; gap: .85rem; margin: 3rem 0 1.1rem;
  padding-bottom: .6rem; scroll-margin-top: 5rem;
  border-bottom: 1px solid var(--linea-fuerte);
  background: linear-gradient(var(--laton), var(--laton)) left bottom / 3.5rem 2px no-repeat; }
div.bloque .num { display: grid; place-items: center; min-width: 2.6rem; height: 2.6rem;
  padding: 0 .55rem; border-radius: .6rem; font-size: 1.3rem; font-style: italic;
  font-weight: 500; color: var(--laton-claro); background: var(--ficha);
  box-shadow: inset 0 0 0 1px rgba(125, 211, 252, .45), 0 8px 20px -8px rgba(33, 85, 208, .7),
    0 0 16px -4px rgba(56, 189, 248, .45); }
/* Títulos de sección en mayúsculas: un poco más chicos y con más aire entre letras, para que
   la serif en altas se lea limpia */
div.bloque .titulo { font-size: 1.5rem; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: var(--tinta); line-height: 1.2; }

/* Indicadores: hoja blanca, etiqueta en versalitas, cifra grande en serif */
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 2rem; }
.kpi { position: relative; overflow: hidden; border-radius: 1rem;
  padding: 1.45rem 1.5rem 1.2rem; color: var(--texto);
  /* Fondo gris claro neón: gris perla que baja a gris acero claro, con un brillo cian muy
     suave por dentro de la orilla */
  background: radial-gradient(90% 70% at 100% 0%, rgba(125, 211, 252, .16), transparent 60%),
              linear-gradient(165deg, #F8FAFC 0%, #EEF2F7 50%, #E3E9F1 100%);
  transition: transform .25s ease, box-shadow .25s ease; }
.kpi { box-shadow: var(--sombra), 0 0 18px -8px var(--marco-luz),
  inset 0 0 24px -10px rgba(56, 189, 248, .35), inset 0 1px 0 rgba(255, 255, 255, .9); }
.kpi:hover { transform: translateY(-2px);
  box-shadow: 0 22px 40px -24px rgba(16, 36, 63, .45), 0 0 22px -8px var(--marco-luz); }
.kpi::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--laton), var(--laton-claro), var(--laton)); }
.kpi-cabeza { display: flex; justify-content: space-between; align-items: center; }
.kpi-etiqueta { display: inline-flex; align-items: baseline; gap: .6rem; font-size: .78rem;
  font-weight: 600; letter-spacing: .12em; text-transform: uppercase;
  color: var(--texto-tenue); }
.kpi-indice { font-size: .8rem; font-weight: 700; letter-spacing: .04em;
  color: var(--laton-t); font-variant-numeric: tabular-nums; }
.kpi-icono, .tarjeta-icono { flex: none; border-radius: 9999px; display: grid;
  place-items: center; color: var(--laton-claro); background: var(--ficha);
  box-shadow: inset 0 0 0 1px rgba(125, 211, 252, .45), 0 6px 16px -6px rgba(33, 85, 208, .7),
    0 0 14px -4px rgba(56, 189, 248, .45); }
.kpi-icono { width: 2.5rem; height: 2.5rem; }
.kpi-icono svg { width: 1.2rem; height: 1.2rem; }
.kpi-valor { font-size: 2.6rem; font-weight: 650; letter-spacing: -.035em; line-height: 1.1;
  margin-top: .75rem; color: var(--tinta); font-variant-numeric: lining-nums tabular-nums;
  font-feature-settings: "tnum" 1, "cv01" 1; }
.kpi-tendencia { display: flex; align-items: center; gap: .6rem; margin-top: .55rem;
  font-size: .82rem; }
.kpi-cambio { display: inline-flex; align-items: center; gap: .3rem; font-weight: 600;
  padding: .1rem .5rem .1rem .4rem; border-radius: .3rem;
  font-variant-numeric: tabular-nums; }
.kpi-cambio.bien { color: var(--verde); background: rgba(29, 118, 88, .08);
  border: 1px solid rgba(29, 118, 88, .25); }
.kpi-cambio.mal { color: var(--vino); background: rgba(156, 47, 62, .07);
  border: 1px solid rgba(156, 47, 62, .25); }
.kpi-cambio svg { width: .9em; height: .9em; }
.kpi-vs { color: var(--texto-tenue); }
/* Fichas secundarias del indicador: dos datos chicos debajo de la cifra */
.kpi-datos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem;
  margin-top: .85rem; }
.kpi-datos > div { min-width: 0; padding: .5rem .7rem; border-radius: .6rem;
  background: rgba(255, 255, 255, .75); border: 1px solid rgba(33, 85, 208, .14); }
.kpi-datos span { display: block; font-size: .68rem; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; color: var(--texto-tenue); white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; }
.kpi-datos b { display: block; margin-top: .15rem; font-size: 1rem; font-weight: 650;
  color: var(--tinta); font-variant-numeric: tabular-nums; }

/* Tarjetas de gráficas (st.container con key="tarjeta_..."): hoja blanca */
div[class*="st-key-tarjeta"] { position: relative; overflow: hidden; background: var(--hoja);
  border-radius: 1rem !important; padding: 1.5rem 1.6rem 1.35rem;
  transition: box-shadow .3s ease; }
div[class*="st-key-tarjeta"]:hover {
  box-shadow: 0 26px 50px -28px rgba(16, 36, 63, .45), 0 0 22px -8px var(--marco-luz); }
.st-key-rango_venta { margin: -.1rem 0 .2rem; }
/* Selector de rango tipo pastilla: riel gris claro y la opción elegida en azul de acción */
.st-key-rango_venta div:has(> button[role="radio"]) { display: inline-flex; gap: .2rem;
  padding: .25rem; border-radius: 9999px; background: var(--riel);
  border: 1px solid var(--linea); }
.st-key-rango_venta button[role="radio"] { border: 0 !important; border-radius: 9999px !important;
  background: transparent; box-shadow: none; min-height: 0; padding: .38rem 1.1rem;
  font-size: .85rem; font-weight: 600; color: var(--texto-suave);
  transition: background .2s ease, color .2s ease, box-shadow .2s ease; }
.st-key-rango_venta button[role="radio"]:hover { color: var(--tinta);
  background: rgba(16, 36, 63, .06); }
.st-key-rango_venta button[aria-checked="true"] { color: #FFFFFF !important;
  background: var(--azul) !important; box-shadow: 0 6px 14px -8px rgba(47, 95, 208, .85); }
.st-key-rango_venta button[aria-checked="true"] * { color: #FFFFFF !important; }
div.tarjeta-titulo { display: flex; align-items: center; gap: .7rem; font-size: 1.45rem;
  font-weight: 600; color: var(--tinta); letter-spacing: -.01em; line-height: 1.3; }
div.tarjeta-titulo .texto { min-width: 0; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; }
.tarjeta-icono { width: 2.2rem; height: 2.2rem; }
/* Acción a la derecha del título: botón redondo con icono para descargar los datos de la
   tarjeta (solo icono, para no quitarle espacio al título) */
div.tarjeta-titulo .accion { margin-left: auto; flex: none; width: 2rem; height: 2rem;
  display: grid; place-items: center; border-radius: 9999px; color: var(--azul) !important;
  text-decoration: none !important; border: 1px solid rgba(47, 95, 208, .25);
  background: var(--hoja); transition: background .2s ease, color .2s ease; }
div.tarjeta-titulo .accion:hover { color: #FFFFFF !important; background: var(--azul); }
div.tarjeta-titulo .accion:focus-visible { outline: 2px solid var(--azul); outline-offset: 2px; }
div.tarjeta-titulo .accion svg { width: 1rem; height: 1rem; }

/* Estado vacío: icono en círculo, título y explicación */
.vacio { display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: .55rem; text-align: center; min-height: 320px; padding: 1.5rem 1rem; }
.vacio-icono { width: 3.3rem; height: 3.3rem; border-radius: 9999px; display: grid;
  place-items: center; color: var(--tinta); background: var(--hoja-tenue);
  border: 1px solid var(--linea); }
.vacio-icono svg { width: 1.5rem; height: 1.5rem; }
.vacio b { font-family: var(--serif); font-size: 1.15rem; font-weight: 600; color: var(--tinta); }
.vacio p { margin: 0; max-width: 36ch; font-size: .9rem; line-height: 1.55;
  color: var(--texto-tenue); }
.vacio code { color: var(--tinta); background: var(--hoja-tenue); }
.tarjeta-icono svg { width: 1.1rem; height: 1.1rem; }
div.tarjeta-nota { font-size: .88rem; color: var(--texto-tenue); line-height: 1.45;
  margin: .2rem 0 .5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.punto { display: inline-block; width: .6rem; height: .6rem; border-radius: 9999px;
  margin: 0 .35rem 0 .35rem; vertical-align: .02rem; }
.raya { display: inline-block; width: 1.1rem; border-top: 2px dashed #5D6779;
  margin: 0 .35rem 0 .45rem; vertical-align: .22rem; }

/* Lectura: nota al margen con filete de latón, como en un informe impreso */
div.lectura { display: flex; align-items: center; margin-top: .3rem; box-sizing: border-box;
  padding: .65rem 1rem; border-radius: .5rem; background: rgba(190, 150, 84, .07);
  border: 1px solid rgba(190, 150, 84, .22); border-left: 3px solid var(--laton);
  font-size: .95rem;
  line-height: 1.5; color: var(--texto); }
div.lectura .txt { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
div.lectura .foco { flex: none; width: 1.85rem; height: 1.85rem; margin-right: .75rem;
  border-radius: 9999px; display: grid; place-items: center; color: var(--laton-t);
  background: rgba(190, 150, 84, .14); }
div.lectura .foco svg { width: 1.05rem; height: 1.05rem; }
div.lectura b { font-weight: 600; color: var(--tinta); }

/* Globos de ayuda de las gráficas (Vega) */
#vg-tooltip-element, .vg-tooltip { font-family: var(--fuente) !important;
  background: #FFFFFF !important; color: var(--texto) !important;
  border: 1px solid var(--linea-fuerte) !important; border-radius: .5rem !important;
  box-shadow: 0 14px 30px -14px rgba(16, 36, 63, .4) !important;
  padding: .55rem .8rem !important; font-size: .85rem !important; }
#vg-tooltip-element td.key, .vg-tooltip td.key { color: var(--texto-tenue) !important; }
#vg-tooltip-element td.value, .vg-tooltip td.value { color: var(--tinta) !important;
  font-weight: 600; }

/* Mapa con esquinas redondeadas y borde fino */
/* El mapa base se tiñe hacia marfil y tinta para integrarse al papel; los puntos de las
   tiendas van en otra capa y conservan su color */
.st-key-tarjeta_mapa .mapboxgl-canvas { filter: sepia(.3) saturate(.75) hue-rotate(-8deg)
  brightness(.98) contrast(.96); }
.st-key-tarjeta_mapa [data-testid="stDeckGlJsonChart"] { border-radius: .7rem;
  overflow: hidden; border: 1px solid var(--linea); }

/* Mini indicadores del mapa */
.minis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem;
  margin: .5rem 0 .9rem; }
.mini { border: 1px solid var(--linea); border-top: 3px solid var(--laton);
  border-radius: .6rem; padding: .85rem 1.05rem .8rem; background: var(--hoja-tenue); }
.mini span { display: block; font-size: .74rem; font-weight: 600; letter-spacing: .1em;
  text-transform: uppercase; color: var(--texto-tenue); }
.mini b { display: block; font-size: 2.1rem; font-weight: 500; color: var(--tinta);
  margin-top: .1rem; font-variant-numeric: lining-nums tabular-nums; }

.stCaption, [data-testid="stCaptionContainer"] { color: var(--texto-tenue) !important; }
/* Colofón: banda de tinta que cierra el informe igual que lo abre el encabezado (sello,
   marca, fuentes, linaje y enlace para volver al inicio) */
div.pie { position: relative; overflow: hidden; margin-top: 3rem; padding: 2.1rem 2rem 1.7rem;
  border-radius: 1rem; text-align: center; color: #DCE6F7; font-size: .86rem; line-height: 1.85;
  background: radial-gradient(60% 140% at 50% 100%, rgba(103, 232, 249, .22), transparent 65%),
              var(--neon-azul); }
/* Encabezado y pie en azul eléctrico con brillo neón suave: filo cian, halo cian alrededor y
   sombra azul que cae */
.encabezado, div.pie { box-shadow: 0 0 0 1px rgba(125, 211, 252, .55),
  0 0 30px -6px rgba(56, 189, 248, .55), 0 22px 48px -24px rgba(33, 85, 208, .75); }
div.pie::before { content: ""; position: absolute; top: 0; left: 2.5rem; right: 2.5rem;
  height: 2px; background: linear-gradient(90deg, transparent, var(--laton-claro), transparent); }
.pie-marca { display: flex; align-items: center; justify-content: center; gap: .75rem;
  margin-bottom: .7rem; }
.pie-marca .sello { width: 2.5rem; height: 2.5rem; border-radius: 9999px; display: grid;
  place-items: center; color: #EED9B0; border: 1px solid rgba(235, 213, 166, .6);
  background: radial-gradient(circle at 32% 28%, #3A78EE, #1838A8 72%); }
.pie-marca .sello svg { width: 1.25rem; height: 1.25rem; }
div.pie .marca { font-size: 1.5rem; font-weight: 600; letter-spacing: -.01em; color: #F6F2EA; }
div.pie .marca small { font-family: var(--fuente) !important; font-size: .6rem; font-weight: 600;
  letter-spacing: .22em; color: var(--laton-claro); border: 1px solid rgba(235, 213, 166, .55);
  border-radius: .25rem; padding: .2rem .15rem .2rem .4rem; margin-left: .55rem;
  vertical-align: .4rem; }
div.pie i { display: inline-block; width: .28rem; height: .28rem; margin: 0 .65rem;
  transform: rotate(45deg); vertical-align: .18rem; background: var(--laton-claro); }
.pie .arriba { display: inline-flex; align-items: center; gap: .4rem; margin-top: 1.1rem;
  padding: .35rem 1.05rem; border-radius: 9999px; font-size: .84rem; font-weight: 500;
  color: #E3E7EE !important; text-decoration: none !important;
  border: 1px solid rgba(255, 255, 255, .18);
  transition: background .2s ease, border-color .2s ease, color .2s ease; }
.pie .arriba:hover { color: #FFFFFF !important; border-color: rgba(235, 213, 166, .7);
  background: rgba(235, 213, 166, .10); }
.encabezado { scroll-margin-top: 1.25rem; }
/* Barra compacta fija: aparece al bajar, cuando el encabezado ya salió de la vista. Es una
   animación ligada al desplazamiento del contenedor principal (solo CSS: Streamlit no permite
   scripts). Donde el navegador no la soporta, la barra simplemente no aparece. */
[data-testid="stMain"] { scroll-timeline: --pagina block; }
.barra { position: fixed; top: .85rem; left: 50%; z-index: 999991;
  width: min(1180px, calc(100% - 2rem)); display: flex; align-items: center;
  justify-content: space-between; gap: 1rem; padding: .4rem .5rem .4rem .45rem;
  border-radius: 9999px; color: #E3E7EE;
  background: linear-gradient(160deg, rgba(24, 56, 168, .96), rgba(33, 85, 208, .96) 55%,
    rgba(26, 114, 207, .96));
  -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
  box-shadow: 0 0 0 1px rgba(125, 211, 252, .55), 0 0 24px -6px rgba(56, 189, 248, .55),
    0 16px 32px -16px rgba(33, 85, 208, .7);
  transform: translate(-50%, -160%); opacity: 0; visibility: hidden; }
@supports (animation-timeline: --pagina) {
  .barra { animation: barra-aparece linear both; animation-timeline: --pagina;
    animation-range: 560px 660px; } }
@keyframes barra-aparece { to { transform: translate(-50%, 0); opacity: 1;
  visibility: visible; } }
.barra-marca { display: inline-flex; align-items: center; gap: .55rem; flex: none;
  font-family: var(--serif); font-size: 1.1rem; font-weight: 600; color: #F6F2EA; }
.barra-marca .sello-mini { width: 2rem; height: 2rem; border-radius: 9999px; display: grid;
  place-items: center; color: #EED9B0; border: 1px solid rgba(235, 213, 166, .55);
  background: radial-gradient(circle at 32% 28%, #3A78EE, #1838A8 72%); }
.barra-marca .sello-mini svg { width: 1.05rem; height: 1.05rem; }
.barra-marca small { font-family: var(--fuente); font-size: .55rem; font-weight: 600;
  letter-spacing: .2em; color: var(--laton-claro); border: 1px solid rgba(235, 213, 166, .5);
  border-radius: .2rem; padding: .15rem .1rem .15rem .3rem; }
.barra-indice { display: flex; gap: .25rem; min-width: 0; overflow-x: auto;
  scrollbar-width: none; }
.barra-indice a { flex: none; display: inline-flex; align-items: center; gap: .4rem;
  font-size: .85rem; font-weight: 500; padding: .32rem .8rem; border-radius: 9999px;
  color: #E3E7EE !important; text-decoration: none !important; transition: background .2s ease; }
.barra-indice a span { font-family: var(--serif); font-style: italic; font-size: 1rem;
  color: var(--laton-claro); }
.barra-indice a:hover { background: rgba(235, 213, 166, .12); color: #FFFFFF !important; }
.barra-indice a:focus-visible { outline: 2px solid var(--laton-claro); outline-offset: 1px; }
.barra-mes { flex: none; padding-right: .7rem; font-size: .72rem; font-weight: 600;
  letter-spacing: .18em; text-transform: uppercase; color: var(--laton-claro); }

/* Separador ornamental antes de las secciones II-IV: filete fino con un rombo de latón */
.ornamento { display: flex; align-items: center; gap: 1rem; width: min(560px, 70%);
  margin: 2.6rem auto 0; }
.ornamento::before, .ornamento::after { content: ""; flex: 1; height: 1px; }
.ornamento::before { background: linear-gradient(90deg, transparent, var(--linea-fuerte)); }
.ornamento::after { background: linear-gradient(90deg, var(--linea-fuerte), transparent); }
.ornamento span { width: .5rem; height: .5rem; transform: rotate(45deg);
  background: var(--laton);
  box-shadow: 0 0 0 4px var(--papel), 0 0 0 5px rgba(190, 150, 84, .45); }
div.bloque.tras-ornamento { margin-top: 1.4rem; }
/* Foco visible al navegar con el teclado (Tab): contorno de latón */
.indice a:focus-visible, .pie .arriba:focus-visible,
.st-key-rango_venta button:focus-visible { outline: 2px solid var(--laton);
  outline-offset: 3px; }

/* Pantallas medianas y chicas: notas y lecturas pueden ocupar dos líneas y todas reservan
   dos (lecturas hasta 2000 px, porque el icono les quita ancho), para que las tarjetas de una
   fila sigan parejas. */
@media (max-width: 2000px) {
  div.lectura .txt { white-space: normal; }
  div.lectura { min-height: 4.7em; } }
@media (max-width: 1600px) {
  div.tarjeta-nota { white-space: normal; min-height: 2.9em; } }
@media (max-width: 1400px) { div.tarjeta-titulo { font-size: 1.28rem; } }
@media (max-width: 1100px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
/* Laptop chica y tableta: la ficha se compacta para caber en una fila; más angosto, se apila */
@media (max-width: 1200px) { .ficha > div { padding: .15rem 1.3rem; }
  .ficha dd { font-size: 1.08rem; } }
@media (max-width: 820px) { .ficha { flex-direction: column; gap: 1.1rem; }
  .ficha > div + div { border-left: 0; } }
@media (max-width: 640px) {
  .block-container { padding: 3.5rem 1rem 2rem; }
  .kpis, .minis { grid-template-columns: 1fr; }
  .encabezado { padding: 2.3rem 1.25rem 1.7rem; gap: 1.6rem; }
  .identidad { gap: .8rem; }
  .emblema { width: 6.2rem; height: 6.2rem; }
  .emblema .centro svg { width: 2.1rem; height: 2.1rem; }
  .encabezado h1 { font-size: 3rem; } .sobretitulo { font-size: .78rem; letter-spacing: .14em; }
  .encabezado .lema { font-size: 1.15rem; } .ficha dd { font-size: 1.08rem; }
  .aviso { flex-direction: column; align-items: flex-start; gap: .5rem; }
  div.bloque .titulo { font-size: 1rem; letter-spacing: .02em; text-wrap: balance; }
  .st-key-rango_venta button[role="radio"] { padding: .32rem .7rem; }
  .saludo .hola { font-size: 1.75rem; } .actualizado { font-size: .76rem; }
  div.tarjeta-titulo .texto { white-space: normal; }
  div.tarjeta-nota, div.lectura { min-height: 0; }
  /* Índice en una sola fila que se desliza con el dedo, con las orillas desvanecidas */
  .indice { flex-wrap: nowrap; justify-content: flex-start; overflow-x: auto; width: 100%;
    scroll-snap-type: x proximity; scrollbar-width: none; padding: .15rem .25rem .35rem;
    -webkit-mask-image: linear-gradient(90deg, transparent, #000 1rem, #000 calc(100% - 1rem),
      transparent);
    mask-image: linear-gradient(90deg, transparent, #000 1rem, #000 calc(100% - 1rem),
      transparent); }
  .indice::-webkit-scrollbar, .barra-indice::-webkit-scrollbar { display: none; }
  .indice a { flex: none; scroll-snap-align: start; }
  .barra { gap: .4rem; } .barra-marca .texto-marca, .barra-mes { display: none; }
  .barra-indice a { padding: .3rem .6rem; font-size: .8rem; }
  .barra-indice { -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 1.2rem),
    transparent); mask-image: linear-gradient(90deg, #000 calc(100% - 1.2rem), transparent); }
  @supports (animation-timeline: --pagina) { .barra { animation-range: 760px 860px; } } }
@media (prefers-reduced-motion: reduce) {
  :root, .encabezado, .aviso, .kpi, div[class*="st-key-tarjeta"], .actualizado .pulso {
    animation: none !important; }
  .kpi, .kpi:hover, div[class*="st-key-tarjeta"], .indice a, .pie .arriba { transition: none;
    transform: none; }
  [data-testid="stMain"] { scroll-behavior: auto; } }
/* Impresión (Ctrl+P o "Guardar como PDF"): papel blanco sin rayas, sombras ni animaciones;
   sin controles; las tarjetas no se parten entre páginas y las bandas de tinta conservan su
   color. */
@media print {
  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #FFFFFF !important; }
  .stApp::before, .encabezado::after { display: none !important; }
  .encabezado, .aviso, .kpi, div[class*="st-key-tarjeta"], div.pie { animation: none !important;
    box-shadow: none !important; border-color: var(--linea-fuerte) !important;
    break-inside: avoid; }
  .encabezado, div.pie, .kpi-icono, .tarjeta-icono, div.bloque .num, .emblema {
    -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .indice, .barra, .pie .arriba, .st-key-rango_venta, [data-testid="stElementToolbar"],
  .tarjeta-titulo .accion, .actualizado .pulso {
    display: none !important; }
  div.bloque { break-after: avoid; } }
</style>
""".replace("__FUENTES__", FUENTES_URL)

st.set_page_config(page_title="AbarrotesPOS", layout="wide")
st.markdown(ESTILOS, unsafe_allow_html=True)


def html(codigo):
    st.markdown(codigo, unsafe_allow_html=True)


def punto(*colores):
    """Punto de leyenda; con varios colores se pinta como degradado."""
    fondo = colores[0] if len(colores) == 1 else f"linear-gradient(90deg, {', '.join(colores)})"
    return f'<span class="punto" style="background:{fondo}"></span>'


def sello(texto):
    """Anillo del emblema: dos círculos finos y el texto siguiendo un círculo de radio 44 entre
    ellos (empieza a la izquierda y sube por arriba). textLength reparte las letras para que el
    texto dé la vuelta completa."""
    return ('<svg class="anillo" viewBox="0 0 120 120" aria-hidden="true">'
            '<circle cx="60" cy="60" r="56"/><circle cx="60" cy="60" r="39"/>'
            '<path id="anillo-sello" d="M16,60 a44,44 0 1,1 88,0 a44,44 0 1,1 -88,0" fill="none"/>'
            f'<text><textPath href="#anillo-sello" textLength="{2 * 3.14159 * 44:.1f}" '
            f'lengthAdjust="spacing">{texto}</textPath></text></svg>')


def bloque(numero, texto):
    """Encabezado de sección: numeral romano en latón y título serif. Desde la II lleva antes
    un separador ornamental (filete con rombo de latón)."""
    clase = "bloque"
    if numero != "I":
        html('<div class="ornamento"><span></span></div>')
        clase += " tras-ornamento"
    html(f'<div class="{clase}" id="seccion-{numero}"><span class="num">{numero}</span>'
         f'<span class="titulo">{texto}</span></div>')


def titulo_tarjeta(dibujo, titulo, nota="", descarga=None):
    """Icono + título + nota de una línea (todas las tarjetas arrancan su gráfica a la misma
    altura). Con descarga=(tabla, archivo), a la derecha del título va un enlace que baja esos
    datos en CSV (el archivo viaja dentro del enlace; no hace falta servidor)."""
    accion = ""
    if descarga is not None:
        tabla, archivo = descarga
        csv = quote(tabla.to_csv(index=False))
        accion = (f'<a class="accion" download="{archivo}" title="Descargar los datos en CSV" '
                  f'aria-label="Descargar los datos en CSV" '
                  f'href="data:text/csv;charset=utf-8,{csv}">{icono("descarga", 2)}</a>')
    html(f'<div class="tarjeta-titulo"><span class="tarjeta-icono">{icono(dibujo)}</span>'
         f'<span class="texto">{titulo}</span>{accion}</div>'
         f'<div class="tarjeta-nota">{nota or "&nbsp;"}</div>')


def vacio(dibujo, titulo, texto):
    """Estado vacío: icono en círculo, título y explicación, en lugar de una gráfica en blanco."""
    html(f'<div class="vacio"><span class="vacio-icono">{icono(dibujo)}</span>'
         f'<b>{titulo}</b><p>{texto}</p></div>')


def lectura(texto):
    """Interpretación de una línea al pie de la gráfica (admite <b>)."""
    html(f'<div class="lectura"><span class="foco">{icono("idea")}</span>'
         f'<span class="txt">{texto}</span></div>')


def icono(nombre, grosor=1.5):
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
    return base.mark_text(color=TEXTO, fontSize=12, fontWeight=600, **lugar).encode(
        text=alt.Text(f"{campo}:Q", format="$,.0f"))


def resalte(campo):
    """Selección al pasar el cursor + opacidad: la barra señalada queda plena y las demás se
    atenúan. Sin cursor encima, todas se ven completas."""
    sel = alt.selection_point(on="pointerover", clear="pointerout", fields=[campo])
    return sel, alt.when(sel).then(alt.value(1.0)).otherwise(alt.value(0.35))


def barras_horizontales(datos, valor, nombre, tooltip, color):
    """Barras horizontales de mayor a menor con su cifra al final (deja aire a la derecha),
    renglones alternos sombreados como libro contable y un rombo de latón en el primer lugar."""
    datos = datos.sort_values(valor, ascending=False).reset_index(drop=True)
    tope = datos[valor].max() * 1.22
    eje_y = alt.Y(f"{nombre}:N", sort=list(datos[nombre]), title=None)
    base = alt.Chart(datos).encode(
        x=alt.X(f"{valor}:Q", title=None, axis=alt.Axis(format="$,.0f"),
                scale=alt.Scale(domainMax=tope)),
        y=eje_y, tooltip=tooltip)
    renglones = alt.Chart(datos.iloc[1::2]).mark_rect(color=TINTA, opacity=.04).encode(
        y=eje_y, x=alt.datum(0), x2=alt.datum(tope))
    primero = alt.Chart(datos.head(1)).mark_point(
        shape="diamond", filled=True, size=80, color=LATON, stroke="white", strokeWidth=1.5,
        opacity=1).encode(y=eje_y, x=alt.datum(datos[valor].max() * .035))
    sel, opacidad = resalte(nombre)
    return (renglones + base.mark_bar(cornerRadiusEnd=3).encode(color=color, opacity=opacidad)
            .add_params(sel) + primero + cifras(base, valor))


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


def tendencia(actual, anterior, etiqueta, sube_es_bueno=True):
    """Chip con flecha y '3.2 %' contra el mismo tramo del mes anterior ('' si no hay con qué
    comparar)."""
    if not anterior:
        return ""
    cambio = (actual - anterior) / anterior * 100
    bien = (cambio >= 0) == sube_es_bueno
    return (f'<div class="kpi-tendencia"><span class="kpi-cambio {"bien" if bien else "mal"}">'
            f'{icono("sube" if cambio >= 0 else "baja", 2.2)}{abs(cambio):.1f} %</span>'
            f'<span class="kpi-vs">vs {etiqueta}</span></div>')


def leer(ruta):
    """CSV opcional: tabla vacía si todavía no se ha generado."""
    return pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()


# --- Datos ----------------------------------------------------------------------------------
diarias = pd.read_csv(ORO / "ventas_diarias.csv", parse_dates=["fecha"])
producto = pd.read_csv(ORO / "ventas_producto_mes.csv")
tiendas = leer(PLATA / "tiendas_zona.csv")
competencia = leer(ORO / "competencia_tienda_piloto.csv")
fiados = leer(ORO / "fiados_por_cliente.csv")

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

# --- Saludo -------------------------------------------------------------------------------
# Fecha y saludo según la hora del servidor; "actualizado" es cuándo corrió el pipeline por
# última vez (fecha del archivo de oro).
ahora = datetime.now()
saludo = ("Buenos días" if ahora.hour < 12 else "Buenas tardes" if ahora.hour < 19
          else "Buenas noches")
hoy = f"{DIAS_LARGOS[ahora.weekday()].capitalize()} {ahora.day} de {MESES[ahora.month - 1]}"
hecho = datetime.fromtimestamp((ORO / "ventas_diarias.csv").stat().st_mtime)
actualizado = f"{hecho.day} {MESES[hecho.month - 1][:3]} {hecho.year}, {hecho:%H:%M}"
html(f"""
<div class="saludo">
  <div>
    <div class="fecha-hoy">{hoy}<i></i><span>Tablero del dueño</span></div>
    <div class="hola">{saludo}, <em>así va tu tienda</em></div>
    <p>{TIENDA_PILOTO["nombre"]} · informe de {nombre_mes}</p>
  </div>
  <div class="actualizado"><span class="pulso"></span>Datos actualizados el {actualizado}</div>
</div>
""")

# --- Encabezado -----------------------------------------------------------------------------
indice = "".join(f'<a href="#seccion-{n}"><span>{n}.</span>{nombre}</a>' for n, nombre in SECCIONES)
html(f"""
<div class="encabezado" id="inicio">
  <div class="identidad">
    <div class="emblema">{sello(f"ABARROTES POS · VILLA DE ÁLVAREZ · {ultimo_mes.year} · ")}
      <span class="centro">{icono("tienda")}</span></div>
    <div class="sobretitulo">Informe mensual de ventas</div>
    <h1>Abarrotes<span class="pos">POS</span></h1>
    <p class="lema">¿Qué vende mi tienda y cuándo vende más?</p>
  </div>
  <dl class="ficha">
    <div><dt>Periodo</dt><dd>{nombre_mes.capitalize()}</dd></div>
    <div><dt>Tienda</dt><dd>{TIENDA_PILOTO["nombre"]}</dd></div>
    <div><dt>Último corte</dt><dd>{periodo}</dd></div>
  </dl>
  <nav class="indice">{indice}</nav>
</div>
<nav class="barra" aria-label="Secciones del informe">
  <span class="barra-marca"><span class="sello-mini">{icono("tienda")}</span>
    <span class="texto-marca">Abarrotes <small>POS</small></span></span>
  <span class="barra-indice">{indice}</span>
  <span class="barra-mes">{nombre_mes}</span>
</nav>
""")

if (diarias["fuente"] == "pos_demo").all():
    html('<div class="aviso"><span class="insignia">Demostración</span><span>Las ventas son '
         "simuladas y se reemplazan por las reales de la tienda piloto en cuanto el dueño las "
         "comparta. El clima y el mapa sí son datos reales.</span></div>")

# --- I. Resumen del mes ---------------------------------------------------------------------
bloque("I", f"Resumen de {nombre_mes}")
venta, ganancia = mes["venta"].sum(), mes["ganancia"].sum()
tickets, fiado = mes["tickets"].sum(), mes["venta_fiado"].sum()
margen = ganancia / venta * 100 if venta else 0
ticket_prom = venta / tickets if tickets else 0
parte_fiado = fiado / venta * 100 if venta else 0
dias_mes = max(mes["fecha"].nunique(), 1)
# (icono, etiqueta, valor, chip de tendencia, dos fichas (etiqueta, dato)). Que el fiado suba
# no es bueno.
indicadores = [
    ("venta", "Venta", pesos(venta), tendencia(venta, anterior["venta"].sum(), vs),
     [("Por día", pesos(venta / dias_mes)),
      ("Mejor día", pesos(mes["venta"].max() if len(mes) else 0))]),
    ("ganancia", "Ganancia", pesos(ganancia), tendencia(ganancia, anterior["ganancia"].sum(), vs),
     [("Margen", f"{margen:.1f} %"), ("Por día", pesos(ganancia / dias_mes))]),
    ("tickets", "Tickets", f"{tickets:,}", tendencia(tickets, anterior["tickets"].sum(), vs),
     [("Por ticket", pesos(ticket_prom)), ("Por día", f"{tickets / dias_mes:,.0f}")]),
    ("fiado", "Vendido a fiado", pesos(fiado),
     tendencia(fiado, anterior["venta_fiado"].sum(), vs, sube_es_bueno=False),
     [("De la venta", f"{parte_fiado:.1f} %"), ("Por día", pesos(fiado / dias_mes))]),
]
html('<div class="kpis">' + "".join(
    f'<div class="kpi"><div class="kpi-cabeza"><span class="kpi-etiqueta">'
    f'<span class="kpi-indice">{n:02d}</span>{etiqueta}</span>'
    f'<span class="kpi-icono">{icono(clave)}</span></div>'
    f'<div class="kpi-valor">{valor}</div>{chip}<div class="kpi-datos">'
    + "".join(f"<div><span>{e}</span><b>{d}</b></div>" for e, d in fichas)
    + "</div></div>"
    for n, (clave, etiqueta, valor, chip, fichas) in enumerate(indicadores, start=1)) + "</div>")

# --- II. Comportamiento de la venta ---------------------------------------------------------
bloque("II", "Comportamiento de la venta")
with st.container(border=True, key="tarjeta_venta_dia"):
    # El promedio se calcula con toda la historia y después se recorta al rango elegido.
    serie = diarias[["fecha", "venta"]].assign(
        promedio=diarias["venta"].rolling(7, min_periods=1).mean())
    titulo_tarjeta("serie", "Venta por día", f"{punto(PIZARRA)}Venta de cada día "
                   f"{punto(AZUL)}Promedio de 7 días", (serie.round(2), "venta_por_dia.csv"))
    rangos = {"3 meses": 3, "6 meses": 6, "12 meses": 12, "Todo": None}
    rango = st.segmented_control("Periodo", list(rangos), default="12 meses",
                                 key="rango_venta", label_visibility="collapsed") or "Todo"
    if rangos[rango]:
        serie = serie[serie["fecha"] > serie["fecha"].max() - pd.DateOffset(months=rangos[rango])]
    meses_corto = str([m[:3] for m in MESES])
    eje_fecha = alt.Axis(tickCount="month", labelExpr=(
        f"{meses_corto}[month(datum.value)] + ' ' + timeFormat(datum.value, '%y')"))
    base = alt.Chart(serie).encode(x=alt.X("fecha:T", title=None, axis=eje_fecha))
    area = base.mark_area(color=degradado("rgba(33,85,208,0)", "rgba(33,85,208,0.12)",
                                          vertical=True)).encode(y="venta:Q")
    diaria = base.mark_line(color=PIZARRA, strokeWidth=1).encode(
        y=alt.Y("venta:Q", title=None, axis=alt.Axis(format="$,.0f")))
    semanal = base.mark_line(color=AZUL, strokeWidth=2.4).encode(y="promedio:Q")
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
              for campo, c in (("venta", ACERO), ("promedio", AZUL))]
    # El mejor día del rango queda marcado en la gráfica (lo explica la lectura de abajo).
    mejor = serie.loc[serie["venta"].idxmax()]
    pico = alt.Chart(serie.loc[[mejor.name]]).encode(x="fecha:T", y="venta:Q")
    pico = (pico.mark_circle(size=80, color=LATON, stroke="white", strokeWidth=2, opacity=1)
            + pico.mark_text(align="left", dx=9, fontSize=12, fontWeight=600, color=LATON_TEXTO,
                             text="Mejor día"))
    st.altair_chart(estilo(alt.layer(area, diaria, semanal, guia, *marcas, pico, selector),
                           ALTO_SERIE))
    lectura(f"Mejor día del periodo: <b>{DIAS_LARGOS[mejor['fecha'].weekday()]} "
            f"{mejor['fecha'].day} de {MESES[mejor['fecha'].month - 1]} de "
            f"{mejor['fecha'].year}</b>, con <b>{pesos(mejor['venta'])}</b>")

col_prod, col_dia, col_evento = st.columns(3, gap="medium")
with col_prod, st.container(border=True, key="tarjeta_productos"):
    top = producto[producto["mes"] == str(ultimo_mes)].nlargest(10, "ganancia")
    titulo_tarjeta("productos", "Productos que más dejan",
                   f"Top 10 por ganancia en {MESES[ultimo_mes.month - 1]} "
                   f"{punto(*ESCALA_TINTA)}Menor a mayor", (top, "productos_top10.csv"))
    # El tono sigue a la ganancia: niebla (menos) -> tinta (más).
    st.altair_chart(estilo(barras_horizontales(
        top, "ganancia", "producto",
        [alt.Tooltip("producto:N", title="Producto"), dinero("ganancia", "Ganancia"),
         alt.Tooltip("piezas:Q", title="Piezas", format=",")],
        alt.Color("ganancia:Q", legend=None, scale=alt.Scale(range=ESCALA_TINTA))), ALTO_FILA))
    if len(top):
        lider = top.iloc[0]
        lectura(f"<b>{lider['producto']}</b> deja el "
                f"<b>{lider['ganancia'] / top['ganancia'].sum() * 100:.0f} %</b> "
                "de la ganancia del top 10")

with col_dia, st.container(border=True, key="tarjeta_dias"):
    # Índice 0-6 = lunes-domingo (sirve para DIAS_LARGOS).
    por_dia = (diarias.groupby("dia_semana")["venta"].mean().reindex(list(DIAS))
               .rename(index=DIAS).rename_axis("dia").reset_index())
    titulo_tarjeta("semana", "Venta por día de la semana",
                   f"Promedio diario {punto(*VERDE_FUERTE)}El más fuerte "
                   f"{punto(*PIZARRA_SUAVE)}Los demás",
                   (por_dia.round(2), "venta_por_dia_semana.csv"))
    fuerte = por_dia.loc[por_dia["venta"].idxmax()]
    sel, opacidad = resalte("dia")
    barras = alt.Chart(por_dia).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("dia:N", sort=list(DIAS.values()), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("venta:Q", title=None, axis=alt.Axis(format="$,.0f")),
        color=alt.condition(alt.datum.venta == fuerte["venta"],
                            alt.value(degradado(*VERDE_FUERTE, vertical=True)),
                            alt.value(degradado(*PIZARRA_SUAVE, vertical=True))),
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

# --- III. Competencia -----------------------------------------------------------------------
bloque("III", "Competencia en la zona")
with st.container(border=True, key="tarjeta_mapa"):
    if len(tiendas):
        aproximada = "" if TIENDA_PILOTO["coordenadas_confirmadas"] else (
            " · ubicación de la tienda piloto aproximada (centro de Villa de Álvarez)")
        titulo_tarjeta("mapa", "Tiendas alrededor de la tienda piloto",
                       f"{punto(LATON)}Tienda piloto y círculo de {RADIO_COMPETENCIA_M} m "
                       f"{punto(VERDE)}Competencia directa {punto(ACERO)}Resto de la zona"
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
            rgb=[rgb(VERDE) if i in cerca else rgb(ACERO, 220) for i in tiendas["osm_id"]])
        piloto = pd.DataFrame({"nombre": [TIENDA_PILOTO["nombre"]], "lat": [TIENDA_PILOTO["lat"]],
                               "lon": [TIENDA_PILOTO["lon"]]})
        blanco = rgb("#FFFFFF")
        capas = [
            pdk.Layer("ScatterplotLayer", piloto, get_position="[lon, lat]",
                      get_radius=RADIO_COMPETENCIA_M, get_fill_color=rgb(LATON, 30),
                      get_line_color=rgb(LATON, 230), stroked=True,
                      line_width_min_pixels=1.5),
            pdk.Layer("ScatterplotLayer", puntos, get_position="[lon, lat]", get_radius=18,
                      radius_min_pixels=5, get_fill_color="rgb", get_line_color=blanco,
                      stroked=True, line_width_min_pixels=1, pickable=True),
            pdk.Layer("ScatterplotLayer", piloto, get_position="[lon, lat]", get_radius=30,
                      radius_min_pixels=9, get_fill_color=rgb(LATON), get_line_color=blanco,
                      stroked=True, line_width_min_pixels=2, pickable=True),
        ]
        vista = pdk.ViewState(latitude=TIENDA_PILOTO["lat"], longitude=TIENDA_PILOTO["lon"],
                              zoom=14.2)
        st.pydeck_chart(pdk.Deck(layers=capas, initial_view_state=vista, map_style=None,
                                 tooltip={"text": "{nombre}", "style": {
                                     "fontFamily": FUENTE, "fontSize": "13px",
                                     "backgroundColor": "#FFFFFF", "color": TINTA,
                                     "border": "1px solid #D5CEC0", "borderRadius": "6px",
                                     "padding": "6px 10px",
                                     "boxShadow": "0 10px 24px -12px rgba(33,85,208,.45)"}}),
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

# --- IV. Clima y crédito --------------------------------------------------------------------
bloque("IV", "Clima y crédito")
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
        esquinas = {"cornerRadiusTopLeft": 4, "cornerRadiusTopRight": 4}
        sel, opacidad = resalte("tramo")
        barras = base.mark_bar(**esquinas).encode(opacity=opacidad, color=alt.Color(
            "tramo:N", legend=None,
            scale=alt.Scale(domain=tramos, range=list(TRAMOS_CALOR.values()))))
        # Brillo blanco que se desvanece hacia arriba: cada barra va de su tono claro al pleno.
        # Es la capa de encima, así que es la que recibe el cursor.
        brillo = base.mark_bar(**esquinas, color=degradado(
            "rgba(255,255,255,0.4)", "rgba(255,255,255,0)", vertical=True)).add_params(sel)
        promedio = alt.Chart(pd.DataFrame({"general": [general]})).mark_rule(
            color=TEXTO_EJE, strokeDash=[5, 4], strokeWidth=1.3).encode(
            y="general:Q", tooltip=[dinero("general", "Promedio de todos los días")])
        contra = base.mark_text(baseline="bottom", dy=-24, fontSize=11, fontWeight=600).encode(
            text="contra_txt:N",
            color=alt.condition(alt.datum.contra >= 0, alt.value(VERDE), alt.value(VINO)))
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
            alt.value(degradado(*VINO_DEGRADADO))), ALTO_FILA))
        parte = deudores["adeudo_bruto"].sum() / fiados["adeudo_bruto"].sum() * 100
        lectura(f"Estos {len(deudores)} clientes suman <b>{pesos(deudores['adeudo_bruto'].sum())}"
                f"</b>, el <b>{parte:.0f} %</b> de todo el fiado")
    else:
        vacio("clientes", "Sin ventas a fiado",
              "Cuando registres ventas a fiado, aquí aparecerán los clientes que más deben.")

# --- Colofón ---------------------------------------------------------------------------------
html(f'<div class="pie"><div class="pie-marca"><span class="sello">{icono("tienda")}</span>'
     '<span class="marca">Abarrotes<small>POS</small></span></div>'
     "<div>Fuentes: punto de venta (demostración)<i></i>Open-Meteo<i></i>"
     "© colaboradores de OpenStreetMap</div>"
     "<div>Linaje: cada cifra sale de data/oro y trae fuente, archivo de bronce y fecha de "
     'captura.</div><a class="arriba" href="#inicio">↑ Volver al inicio</a></div>')
