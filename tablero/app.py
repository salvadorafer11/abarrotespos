"""Tablero de AbarrotesPOS para el dueño de la tienda.  streamlit run tablero/app.py

Estilo claro y vivo: fondo blanco azulado con una aurora pastel que deriva muy despacio,
tarjetas de vidrio blanco, Bricolage Grotesque (títulos y cifras) y Figtree (texto). Cada
sección y cada tarjeta combinan un par de colores de la PALETA. Streamlit quita las etiquetas
<script>, así que todo el diseño va en ESTILOS; el tema base vive en .streamlit/config.toml.

Cada tarjeta tiene título de una línea, nota de una línea y gráfica de altura fija, para que
las tarjetas de una misma fila midan lo mismo.
"""

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
ORO = RAIZ / "data" / "oro"
PLATA = RAIZ / "data" / "plata"
sys.path.insert(0, str(RAIZ))
from extractores.config import RADIO_COMPETENCIA_M, TIENDA_PILOTO  # noqa: E402

# --- PALETA: colores vivos sobre fondo claro --------------------------------------------------
ZAFIRO = "#4F6BED"  # dato principal
ESMERALDA = "#10A37F"  # competencia, ganancia
CUARZO = "#E5578A"  # rosa: promedio de 7 días, fiado
AMATISTA = "#8B5CF6"
JADE = "#0EA5A0"
AMBAR = "#E0911F"  # tienda piloto
TINTA = "#1B2132"  # texto principal
TEXTO = "#2A3145"
TEXTO_EJE = "#566079"
REJILLA = "rgba(27, 33, 50, 0.07)"
FUENTE = "Figtree, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
# Degradados de varios tonos: días con evento / día más fuerte y días normales.
ESMERALDA_FUERTE = ("#047857", "#059669", "#10B981", "#34D399")
ESMERALDA_CLARO = ("#6EDDB4", "#9BE8CB", "#C3F2DF")
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

# Iconos (Heroicons, MIT) para las tarjetas de indicadores.
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
}

# Bricolage Grotesque (títulos y cifras: carácter propio) + Figtree (texto: muy legible).
FUENTES_URL = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,"
               "500..800&family=Figtree:wght@400..700&display=swap")

ESTILOS = """
<style>
@import url('__FUENTES__');
:root {
  /* Colores vivos como tripletas RGB: rgba(var(--x), .5) */
  --zafiro: 79, 107, 237; --esmeralda: 16, 163, 127; --cuarzo: 229, 87, 138;
  --amatista: 139, 92, 246; --jade: 14, 165, 160; --ambar: 224, 145, 31;
  /* Tintas: versión profunda de cada color para texto (contraste AA sobre blanco) */
  --zafiro-t: #3047C9; --esmeralda-t: #08745A; --cuarzo-t: #B8285F; --amatista-t: #6D3FD9;
  --tinta: #1B2132; --texto: #2A3145; --texto-suave: #4A536A; --texto-tenue: #646D86;
  --vidrio: rgba(255, 255, 255, .78); --borde: rgba(27, 33, 50, .08);
  --sombra: 0 1px 2px rgba(27, 33, 50, .04), 0 14px 34px -16px rgba(41, 52, 98, .24);
  --fuente: Figtree, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
  --titular: 'Bricolage Grotesque', Figtree, ui-sans-serif, sans-serif;
  --arcoiris: linear-gradient(90deg, rgb(var(--zafiro)), rgb(var(--amatista)),
    rgb(var(--cuarzo)), rgb(var(--ambar)), rgb(var(--esmeralda)), rgb(var(--zafiro)));
  /* Marco de todos los elementos: su color y un halo suave del mismo tono */
  --marco-luz: color-mix(in srgb, var(--marco) 32%, transparent);
  --sombra-marco: var(--sombra), 0 0 22px -8px var(--marco-luz);
}
/* Marco de color: un solo color que recorre la paleta y es el mismo en todos los elementos a la
   vez, porque se anima una sola variable en la raíz. Cambia en pasos (10 por segundo) para no
   recalcular la página en cada cuadro. */
@property --marco { syntax: '<color>'; inherits: true; initial-value: #4F6BED; }
:root { animation: marco 30s steps(60) infinite; }
@keyframes marco { 0%, 100% { --marco: #4F6BED; } 20% { --marco: #8B5CF6; }
  40% { --marco: #E5578A; } 60% { --marco: #E0911F; } 80% { --marco: #10A37F; } }
.stApp, .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"],
.stApp button { font-family: var(--fuente) !important; }
.encabezado h1, .kpi-valor, .mini b, div.tarjeta-titulo, div.bloque .num, .kpi-indice,
div.pie .marca { font-family: var(--titular) !important; }
::selection { background: rgba(var(--amatista), .2); color: var(--tinta); }
.stApp, .stApp * { scrollbar-width: thin; scrollbar-color: rgba(27, 33, 50, .2) transparent; }

/* Fondo claro con aurora: manchas pastel de los seis colores que derivan muy despacio
   (60 s por ciclo). Se anima solo con transform, que no recarga la página. */
.stApp { background: #F4F6FB; color: var(--texto); isolation: isolate;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }
.stApp::before { content: ""; position: fixed; inset: -25%; z-index: -1; pointer-events: none;
  background:
    radial-gradient(30% 36% at 22% 24%, rgba(var(--zafiro), .20), transparent 70%),
    radial-gradient(28% 34% at 78% 20%, rgba(var(--cuarzo), .16), transparent 70%),
    radial-gradient(32% 38% at 74% 76%, rgba(var(--esmeralda), .16), transparent 70%),
    radial-gradient(28% 34% at 24% 78%, rgba(var(--amatista), .16), transparent 70%),
    radial-gradient(20% 24% at 50% 50%, rgba(var(--ambar), .10), transparent 70%);
  animation: aurora 60s ease-in-out infinite alternate; will-change: transform; }
@keyframes aurora {
  0% { transform: translate3d(0, 0, 0) rotate(0deg) scale(1); }
  50% { transform: translate3d(4%, -3%, 0) rotate(10deg) scale(1.06); }
  100% { transform: translate3d(-4%, 3%, 0) rotate(-8deg) scale(1.02); } }
@keyframes corrimiento { to { background-position: 200% center; } }
[data-testid="stHeader"] { background: transparent; }

/* Ancho: el contenido ocupa casi toda la pantalla en computadora (tope 1760 px). */
.block-container { max-width: 1760px; padding: 3.75rem 2rem 2.5rem; }

/* Marco de color compartido */
.encabezado, .aviso, .kpi, div[class*="st-key-tarjeta"] {
  border: 2px solid var(--marco) !important; box-shadow: var(--sombra-marco); }

/* Encabezado: vidrio blanco y título con degradado vivo */
.encabezado { position: relative; overflow: hidden; border-radius: 1.5rem;
  margin-bottom: 1.1rem; padding: 2.1rem 2rem 1.8rem; display: flex; flex-direction: column;
  align-items: center; text-align: center; gap: .65rem;
  background: radial-gradient(50% 120% at 50% 0%, rgba(var(--amatista), .08), transparent 70%),
              var(--vidrio); }
.sobretitulo { font-size: .76rem; font-weight: 700; letter-spacing: .14em;
  text-transform: uppercase; color: var(--zafiro-t); background: rgba(var(--zafiro), .08);
  border: 1px solid rgba(var(--zafiro), .18); border-radius: 9999px; padding: .32rem 1rem; }
.sobretitulo em { font-style: normal; text-transform: none; letter-spacing: .01em;
  font-weight: 600; color: var(--amatista-t); }
.encabezado h1 { font-size: 3.4rem; font-weight: 800; letter-spacing: -.035em;
  line-height: 1.08; margin: .15rem 0 0; padding: 0 .1em;
  background: linear-gradient(90deg, var(--zafiro-t), var(--amatista-t), var(--cuarzo-t),
    var(--amatista-t), var(--zafiro-t));
  background-size: 200% auto; -webkit-background-clip: text; background-clip: text;
  color: transparent !important; -webkit-text-fill-color: transparent;
  animation: corrimiento 16s linear infinite; }
.encabezado .lema { color: var(--texto-suave); margin: 0; font-size: 1.12rem;
  font-weight: 500; }
.encabezado .periodo { display: inline-flex; align-items: center; justify-content: center;
  flex-wrap: wrap; gap: .35rem .75rem; color: var(--texto-suave); font-size: .92rem;
  line-height: 1.4; }
.encabezado .periodo b { font-weight: 700; color: var(--tinta); }
.encabezado .periodo i { width: .4rem; height: .4rem; border-radius: 9999px;
  background: linear-gradient(135deg, rgb(var(--cuarzo)), rgb(var(--ambar))); }

/* Aviso: vidrio blanco */
.aviso { display: flex; align-items: center; gap: .9rem; background: var(--vidrio);
  border-radius: 1rem; padding: .75rem 1.1rem; color: var(--texto-suave); font-size: .95rem;
  line-height: 1.5; margin-bottom: .4rem; }
.aviso code { color: var(--zafiro-t); background: rgba(var(--zafiro), .08); }
.insignia { flex: none; font-size: .72rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; border-radius: 9999px; padding: .22rem .7rem;
  color: var(--cuarzo-t); background: rgba(var(--cuarzo), .1);
  border: 1px solid rgba(var(--cuarzo), .3); }

/* Secciones: número romano en una ficha con el degradado propio de cada sección */
div.bloque { display: flex; align-items: center; gap: .8rem; margin: 2.6rem 0 .8rem;
  font-size: .88rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
  color: var(--tinta); }
div.bloque .num { display: grid; place-items: center; min-width: 2.2rem; height: 2.2rem;
  padding: 0 .55rem; border-radius: .75rem; font-size: 1rem; font-weight: 700;
  letter-spacing: 0; color: #fff;
  background: linear-gradient(135deg, rgb(var(--c1)), rgb(var(--c2)));
  box-shadow: 0 8px 16px -8px rgba(var(--c1), .8); }
div.bloque::after { content: ""; flex: 1; height: 2px; border-radius: 2px;
  background: linear-gradient(90deg, rgba(var(--c1), .5), rgba(var(--c2), .25) 40%,
    transparent 85%); }
div.b-I { --c1: var(--zafiro); --c2: var(--amatista); }
div.b-II { --c1: var(--amatista); --c2: var(--cuarzo); }
div.b-III { --c1: var(--esmeralda); --c2: var(--jade); }
div.b-IV { --c1: var(--ambar); --c2: var(--cuarzo); }

/* Indicadores: vidrio blanco con dos destellos de su par de colores (--acento y --segundo
   llegan en el style de cada tarjeta) e icono en ficha con degradado */
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1.4rem;
  padding: .4rem 0; }
.kpi { position: relative; overflow: hidden; border-radius: 1.3rem;
  padding: 1.4rem 1.45rem 1.25rem; color: var(--texto);
  background:
    radial-gradient(90% 120% at 100% 0%, rgba(var(--acento), .15), transparent 60%),
    radial-gradient(80% 110% at 0% 100%, rgba(var(--segundo), .11), transparent 60%),
    var(--vidrio);
  transition: transform .25s ease, box-shadow .25s ease; }
.kpi:hover { transform: translateY(-3px);
  box-shadow: 0 22px 40px -18px rgba(var(--acento), .5), 0 0 26px -6px var(--marco-luz); }
.kpi-cabeza { display: flex; justify-content: space-between; align-items: center; }
.kpi-etiqueta { display: inline-flex; align-items: baseline; gap: .55rem; font-size: .8rem;
  font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
  color: var(--texto-suave); }
.kpi-indice { font-size: .95rem; font-weight: 700; letter-spacing: 0;
  color: rgb(var(--acento)); filter: brightness(.78) saturate(1.2); }
.kpi-icono { width: 2.5rem; height: 2.5rem; border-radius: .85rem; display: grid;
  place-items: center; color: #fff;
  background: linear-gradient(135deg, rgb(var(--acento)), rgb(var(--segundo)));
  box-shadow: 0 10px 18px -10px rgba(var(--acento), .9); }
.kpi-icono svg { width: 1.25rem; height: 1.25rem; }
.kpi-valor { font-size: 2.6rem; font-weight: 700; letter-spacing: -.035em; line-height: 1.1;
  margin-top: .6rem; color: var(--tinta); font-variant-numeric: tabular-nums; }
.kpi-tendencia { display: flex; align-items: center; gap: .55rem; margin-top: .5rem;
  font-size: .82rem; }
.kpi-cambio { font-weight: 700; padding: .12rem .55rem; border-radius: 9999px;
  font-variant-numeric: tabular-nums; }
.kpi-cambio.bien { color: var(--esmeralda-t); background: rgba(var(--esmeralda), .12);
  border: 1px solid rgba(var(--esmeralda), .28); }
.kpi-cambio.mal { color: var(--cuarzo-t); background: rgba(var(--cuarzo), .1);
  border: 1px solid rgba(var(--cuarzo), .28); }
.kpi-vs { color: var(--texto-tenue); }
.kpi-ayuda { font-size: .9rem; line-height: 1.5; color: var(--texto-tenue);
  margin-top: .65rem; padding-top: .6rem; border-top: 1px solid var(--borde); }
.kpi-ayuda b { color: var(--tinta); font-weight: 700; }

/* Tarjetas de gráficas (st.container con key="tarjeta_..."): vidrio blanco con dos destellos
   de su par de colores en esquinas opuestas */
div[class*="st-key-tarjeta"] { position: relative; overflow: hidden;
  border-radius: 1.35rem !important; padding: 1.5rem 1.55rem 1.3rem;
  background: radial-gradient(60% 80% at 100% 0%, rgba(var(--tono), .10), transparent 65%),
              radial-gradient(50% 70% at 0% 100%, rgba(var(--tono2), .07), transparent 65%),
              var(--vidrio); }
.st-key-tarjeta_venta_dia { --tono: var(--zafiro); --tono2: var(--cuarzo); }
.st-key-tarjeta_productos { --tono: var(--amatista); --tono2: var(--esmeralda); }
.st-key-tarjeta_dias { --tono: var(--zafiro); --tono2: var(--esmeralda); }
.st-key-tarjeta_eventos { --tono: var(--esmeralda); --tono2: var(--jade); }
.st-key-tarjeta_mapa { --tono: var(--esmeralda); --tono2: var(--ambar); }
.st-key-tarjeta_clima { --tono: 93, 173, 236; --tono2: 234, 90, 44; }  /* frío -> calor */
.st-key-tarjeta_fiado { --tono: var(--cuarzo); --tono2: var(--amatista); }
.st-key-rango_venta { margin: -.1rem 0 .2rem; }
.st-key-rango_venta button { font-size: .85rem; }
div.tarjeta-titulo { font-size: 1.34rem; font-weight: 700; color: var(--tinta);
  letter-spacing: -.02em; line-height: 1.3; }
div.tarjeta-nota { font-size: .9rem; color: var(--texto-tenue); line-height: 1.45;
  margin: .15rem 0 .45rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.punto { display: inline-block; width: .6rem; height: .6rem; border-radius: 9999px;
  margin: 0 .35rem 0 .3rem; vertical-align: .02rem; }
.raya { display: inline-block; width: 1.1rem; border-top: 2px dashed #566079;
  margin: 0 .35rem 0 .45rem; vertical-align: .22rem; }

/* Lectura: interpretación al pie de cada gráfica, en una caja teñida del color de la tarjeta */
div.lectura { display: flex; align-items: flex-start; gap: .6rem; margin-top: .3rem;
  box-sizing: border-box; padding: .65rem .9rem; border-radius: .9rem;
  background: linear-gradient(90deg, rgba(var(--tono), .08), rgba(var(--tono2), .05));
  border: 1px solid rgba(var(--tono), .14); font-size: .95rem; line-height: 1.5;
  color: var(--texto); }
div.lectura::before { content: ""; flex: none; width: .5rem; height: .5rem; margin-top: .5em;
  border-radius: 9999px;
  background: linear-gradient(135deg, rgb(var(--tono)), rgb(var(--tono2))); }
div.lectura span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
div.lectura b { font-weight: 700; color: var(--tinta); }

/* Globos de ayuda de las gráficas (Vega) */
#vg-tooltip-element, .vg-tooltip { font-family: var(--fuente) !important;
  background: rgba(255, 255, 255, .97) !important; color: var(--texto) !important;
  border: 1px solid rgba(var(--amatista), .25) !important; border-radius: .7rem !important;
  box-shadow: 0 14px 30px -12px rgba(41, 52, 98, .35) !important;
  padding: .55rem .8rem !important; font-size: .85rem !important; }
#vg-tooltip-element td.key, .vg-tooltip td.key { color: var(--texto-tenue) !important; }
#vg-tooltip-element td.value, .vg-tooltip td.value { color: var(--tinta) !important;
  font-weight: 700; }

/* Mapa con esquinas redondeadas y borde fino */
.st-key-tarjeta_mapa [data-testid="stDeckGlJsonChart"] { border-radius: 1rem;
  overflow: hidden; border: 1px solid var(--borde); }

/* Mini indicadores del mapa */
.minis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem;
  margin: .45rem 0 .85rem; }
.mini { position: relative; overflow: hidden; border: 1px solid var(--borde);
  border-radius: 1rem; padding: .85rem 1.05rem .8rem;
  background: radial-gradient(70% 140% at 0% 0%, rgba(var(--tono), .12), transparent 70%),
              rgba(255, 255, 255, .7); }
.mini::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: rgb(var(--tono)); }
.mini:nth-child(1) { --tono: var(--esmeralda); }
.mini:nth-child(2) { --tono: var(--zafiro); }
.mini:nth-child(3) { --tono: var(--ambar); }
.mini span { display: block; font-size: .78rem; font-weight: 700; letter-spacing: .08em;
  text-transform: uppercase; color: var(--texto-tenue); }
.mini b { display: block; font-size: 1.9rem; font-weight: 700; color: var(--tinta);
  letter-spacing: -.03em; margin-top: .15rem; font-variant-numeric: tabular-nums; }

.stCaption, [data-testid="stCaptionContainer"] { color: var(--texto-tenue) !important; }
/* Colofón */
div.pie { font-size: .85rem; color: var(--texto-tenue); text-align: center;
  margin-top: 2.4rem; line-height: 1.8; }
div.pie::before { content: ""; display: block; width: min(420px, 70%); height: 3px;
  margin: 0 auto 1rem; border-radius: 3px; background: var(--arcoiris); opacity: .7; }
div.pie .marca { font-size: 1.1rem; font-weight: 800; letter-spacing: -.02em;
  background: linear-gradient(90deg, var(--zafiro-t), var(--amatista-t), var(--cuarzo-t));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
div.pie i { display: inline-block; width: .3rem; height: .3rem; margin: 0 .6rem;
  border-radius: 9999px; vertical-align: .18rem; background: rgba(var(--amatista), .5); }

/* Pantallas medianas y chicas. Laptop: notas y lecturas pueden ocupar dos líneas y todas
   reservan dos, para que las tarjetas de una fila sigan parejas. */
@media (max-width: 1600px) {
  div.tarjeta-nota { white-space: normal; min-height: 2.9em; }
  div.lectura span { white-space: normal; }
  div.lectura { min-height: 4.6em; } }
@media (max-width: 1400px) { div.tarjeta-titulo { font-size: 1.18rem; } }
@media (max-width: 1100px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) {
  .block-container { padding: 3.5rem 1rem 2rem; }
  .kpis, .minis { grid-template-columns: 1fr; }
  .encabezado { padding: 1.7rem 1rem 1.4rem; }
  .encabezado h1 { font-size: 2.5rem; } .sobretitulo { letter-spacing: .08em; }
  .encabezado .periodo { flex-direction: column; gap: .1rem; }
  .encabezado .periodo i { display: none; }
  div.tarjeta-nota, div.lectura { min-height: 0; } }
@media (prefers-reduced-motion: reduce) {
  :root, .stApp::before, .encabezado h1 { animation: none !important; }
  .kpi, .kpi:hover { transition: none; transform: none; } }
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


def bloque(numero, texto):
    """Etiqueta de sección numerada con romanos; cada sección tiene su par de colores."""
    html(f'<div class="bloque b-{numero}"><span class="num">{numero}</span><span>{texto}</span>'
         "</div>")


def titulo_tarjeta(titulo, nota=""):
    """Título + nota de una línea: todas las tarjetas arrancan su gráfica a la misma altura."""
    html(f'<div class="tarjeta-titulo">{titulo}</div>'
         f'<div class="tarjeta-nota">{nota or "&nbsp;"}</div>')


def lectura(texto):
    """Interpretación de una línea al pie de la gráfica (admite <b>)."""
    html(f'<div class="lectura"><span>{texto}</span></div>')


def icono(nombre):
    return ('<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
            'stroke-width="1.6" stroke="currentColor" aria-hidden="true">'
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
    """Barras horizontales de mayor a menor con su cifra al final; deja aire a la derecha."""
    base = alt.Chart(datos).encode(
        x=alt.X(f"{valor}:Q", title=None, axis=alt.Axis(format="$,.0f"),
                scale=alt.Scale(domainMax=datos[valor].max() * 1.22)),
        y=alt.Y(f"{nombre}:N", sort="-x", title=None), tooltip=tooltip)
    sel, opacidad = resalte(nombre)
    return (base.mark_bar(cornerRadiusEnd=4).encode(color=color, opacity=opacidad)
            .add_params(sel) + cifras(base, valor))


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
    """Chip '▲ 3.2 %' contra el mismo tramo del mes anterior ('' si no hay con qué comparar)."""
    if not anterior:
        return ""
    cambio = (actual - anterior) / anterior * 100
    bien = (cambio >= 0) == sube_es_bueno
    return (f'<div class="kpi-tendencia"><span class="kpi-cambio {"bien" if bien else "mal"}">'
            f'{"▲" if cambio >= 0 else "▼"} {abs(cambio):.1f} %</span>'
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

# --- Encabezado -----------------------------------------------------------------------------
html(f"""
<div class="encabezado">
  <div class="sobretitulo">Informe de ventas · <em>{nombre_mes}</em></div>
  <h1>AbarrotesPOS</h1>
  <p class="lema">¿Qué vende mi tienda y cuándo vende más?</p>
  <div class="periodo"><b>{TIENDA_PILOTO["nombre"]}</b><i></i><span>Último corte: {periodo}</span>
  </div>
</div>
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
# (icono, etiqueta, valor, ayuda, par de colores, chip de tendencia). Que el fiado suba no es
# bueno.
indicadores = [
    ("venta", "Venta", pesos(venta), "Total cobrado en el periodo", ("zafiro", "amatista"),
     tendencia(venta, anterior["venta"].sum(), vs)),
    ("ganancia", "Ganancia", pesos(ganancia), f"Margen de <b>{margen:.1f} %</b> sobre la venta",
     ("esmeralda", "jade"), tendencia(ganancia, anterior["ganancia"].sum(), vs)),
    ("tickets", "Tickets", f"{tickets:,}", f"Ticket promedio de <b>{pesos(ticket_prom)}</b>",
     ("cuarzo", "amatista"), tendencia(tickets, anterior["tickets"].sum(), vs)),
    ("fiado", "Vendido a fiado", pesos(fiado), f"<b>{parte_fiado:.1f} %</b> de la venta, por "
     "cobrar", ("ambar", "cuarzo"),
     tendencia(fiado, anterior["venta_fiado"].sum(), vs, sube_es_bueno=False)),
]
html('<div class="kpis">' + "".join(
    f'<div class="kpi" style="--acento: var(--{c1}); --segundo: var(--{c2})">'
    f'<div class="kpi-cabeza"><span class="kpi-etiqueta"><span class="kpi-indice">'
    f'{n:02d}</span>{etiqueta}</span><span class="kpi-icono">{icono(clave)}</span></div>'
    f'<div class="kpi-valor">{valor}</div>{chip}<div class="kpi-ayuda">{ayuda}</div></div>'
    for n, (clave, etiqueta, valor, ayuda, (c1, c2), chip) in enumerate(indicadores, start=1))
    + "</div>")

# --- II. Comportamiento de la venta ---------------------------------------------------------
bloque("II", "Comportamiento de la venta")
with st.container(border=True, key="tarjeta_venta_dia"):
    titulo_tarjeta("Venta por día", f"{punto(ZAFIRO)}Venta de cada día "
                   f"{punto(CUARZO)}Promedio de 7 días")
    # El promedio se calcula con toda la historia y después se recorta al rango elegido.
    serie = diarias[["fecha", "venta"]].assign(
        promedio=diarias["venta"].rolling(7, min_periods=1).mean())
    rangos = {"3 meses": 3, "6 meses": 6, "12 meses": 12, "Todo": None}
    rango = st.segmented_control("Periodo", list(rangos), default="12 meses",
                                 key="rango_venta", label_visibility="collapsed") or "Todo"
    if rangos[rango]:
        serie = serie[serie["fecha"] > serie["fecha"].max() - pd.DateOffset(months=rangos[rango])]
    meses_corto = str([m[:3] for m in MESES])
    eje_fecha = alt.Axis(tickCount="month", labelExpr=(
        f"{meses_corto}[month(datum.value)] + ' ' + timeFormat(datum.value, '%y')"))
    base = alt.Chart(serie).encode(x=alt.X("fecha:T", title=None, axis=eje_fecha))
    area = base.mark_area(opacity=0.22, color=degradado(
        "rgba(139,92,246,0)", AMATISTA, ZAFIRO, vertical=True)).encode(y="venta:Q")
    diaria = base.mark_line(color=ZAFIRO, strokeWidth=1.2, opacity=0.75).encode(
        y=alt.Y("venta:Q", title=None, axis=alt.Axis(format="$,.0f")))
    semanal = base.mark_line(color=CUARZO, strokeWidth=2.6).encode(y="promedio:Q")
    # Guía al pasar el cursor: el día más cercano muestra una línea vertical, un punto en cada
    # serie y un solo globo con la venta y el promedio de ese día.
    cursor = alt.selection_point(nearest=True, on="pointerover", clear="pointerout",
                                 fields=["fecha"], empty=False)
    selector = base.mark_point(opacity=0).encode(
        y="venta:Q", tooltip=[alt.Tooltip("fecha:T", title="Fecha", format="%d/%m/%Y"),
                              dinero("venta", "Venta"), dinero("promedio", "Promedio 7 días")]
    ).add_params(cursor)
    guia = base.mark_rule(color=TEXTO_EJE, strokeDash=[4, 3]).transform_filter(cursor)
    marcas = [base.mark_circle(size=70, color=c, stroke="white", strokeWidth=2)
              .encode(y=f"{campo}:Q").transform_filter(cursor)
              for campo, c in (("venta", ZAFIRO), ("promedio", CUARZO))]
    # El mejor día del rango queda marcado en la gráfica (lo explica la lectura de abajo).
    mejor = serie.loc[serie["venta"].idxmax()]
    pico = alt.Chart(serie.loc[[mejor.name]]).encode(x="fecha:T", y="venta:Q")
    pico = (pico.mark_circle(size=90, color=AMBAR, stroke="white", strokeWidth=2, opacity=1)
            + pico.mark_text(align="left", dx=9, fontSize=12, fontWeight=700, color="#A35F00",
                             text="Mejor día"))
    st.altair_chart(estilo(alt.layer(area, diaria, semanal, guia, *marcas, pico, selector),
                           ALTO_SERIE))
    lectura(f"Mejor día del periodo: <b>{DIAS_LARGOS[mejor['fecha'].weekday()]} "
            f"{mejor['fecha'].day} de {MESES[mejor['fecha'].month - 1]} de "
            f"{mejor['fecha'].year}</b>, con <b>{pesos(mejor['venta'])}</b>")

col_prod, col_dia, col_evento = st.columns(3, gap="large")
with col_prod, st.container(border=True, key="tarjeta_productos"):
    titulo_tarjeta("Productos que más dejan",
                   f"Top 10 por ganancia en {MESES[ultimo_mes.month - 1]} "
                   f"{punto(AMATISTA, ZAFIRO, JADE, ESMERALDA)}Menor a mayor")
    top = producto[producto["mes"] == str(ultimo_mes)].nlargest(10, "ganancia")
    # El color sigue a la ganancia: amatista (menos) -> zafiro -> jade -> esmeralda (más).
    st.altair_chart(estilo(barras_horizontales(
        top, "ganancia", "producto",
        [alt.Tooltip("producto:N", title="Producto"), dinero("ganancia", "Ganancia"),
         alt.Tooltip("piezas:Q", title="Piezas", format=",")],
        alt.Color("ganancia:Q", legend=None,
                  scale=alt.Scale(range=[AMATISTA, ZAFIRO, JADE, ESMERALDA]))), ALTO_FILA))
    if len(top):
        lider = top.iloc[0]
        lectura(f"<b>{lider['producto']}</b> deja el "
                f"<b>{lider['ganancia'] / top['ganancia'].sum() * 100:.0f} %</b> "
                "de la ganancia del top 10")

with col_dia, st.container(border=True, key="tarjeta_dias"):
    titulo_tarjeta("Venta por día de la semana",
                   f"Promedio diario {punto(*ESMERALDA_FUERTE)}El más fuerte "
                   f"{punto(AMATISTA, ZAFIRO)}Los demás")
    # Índice 0-6 = lunes-domingo (sirve para DIAS_LARGOS).
    por_dia = (diarias.groupby("dia_semana")["venta"].mean().reindex(list(DIAS))
               .rename(index=DIAS).rename_axis("dia").reset_index())
    fuerte = por_dia.loc[por_dia["venta"].idxmax()]
    barras = alt.Chart(por_dia).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("dia:N", sort=list(DIAS.values()), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("venta:Q", title=None, axis=alt.Axis(format="$,.0f")),
        color=alt.condition(alt.datum.venta == fuerte["venta"],
                            alt.value(degradado(*ESMERALDA_FUERTE, vertical=True)),
                            alt.value(degradado(AMATISTA, ZAFIRO, vertical=True))),
        tooltip=[alt.Tooltip("dia:N", title="Día"), dinero("venta", "Venta promedio")])
    sel, opacidad = resalte("dia")
    st.altair_chart(estilo(barras.encode(opacity=opacidad).add_params(sel), ALTO_FILA))
    extra =(fuerte["venta"] / por_dia["venta"].iloc[:5].mean() - 1) * 100
    lectura(f"El <b>{DIAS_LARGOS[fuerte.name]}</b> vende <b>{extra:.0f} % más</b> que un día "
            "entre semana")

with col_evento, st.container(border=True, key="tarjeta_eventos"):
    titulo_tarjeta("Días con evento vs días normales",
                   f"Venta promedio por día {punto(*ESMERALDA_FUERTE)}Con evento "
                   f"{punto(*ESMERALDA_CLARO)}Normal")
    eventos = (diarias.assign(evento=diarias["evento"].fillna("").replace("", "normal"))
               .groupby("evento")["venta"].agg(promedio="mean", dias="count").reset_index())
    eventos["nombre"] = eventos["evento"].map(EVENTOS).fillna(eventos["evento"])
    st.altair_chart(estilo(barras_horizontales(
        eventos, "promedio", "nombre",
        [alt.Tooltip("nombre:N", title="Tipo de día"), dinero("promedio", "Venta promedio"),
         alt.Tooltip("dias:Q", title="Días")],
        alt.condition(alt.datum.evento == "normal", alt.value(degradado(*ESMERALDA_CLARO)),
                      alt.value(degradado(*ESMERALDA_FUERTE)))), ALTO_FILA))
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
        titulo_tarjeta("Tiendas alrededor de la tienda piloto",
                       f"{punto(AMBAR)}Tienda piloto y círculo de {RADIO_COMPETENCIA_M} m "
                       f"{punto(ESMERALDA)}Competencia directa {punto(ZAFIRO)}Resto de la zona"
                       f"{aproximada}")
        cercana = f"{competencia['distancia_m'].min():,.0f} m" if len(competencia) else "—"
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
            rgb=[rgb(ESMERALDA) if i in cerca else rgb(ZAFIRO, 220) for i in tiendas["osm_id"]])
        piloto = pd.DataFrame({"nombre": [TIENDA_PILOTO["nombre"]], "lat": [TIENDA_PILOTO["lat"]],
                               "lon": [TIENDA_PILOTO["lon"]]})
        blanco = rgb("#FFFFFF")
        capas = [
            pdk.Layer("ScatterplotLayer", piloto, get_position="[lon, lat]",
                      get_radius=RADIO_COMPETENCIA_M, get_fill_color=rgb(AMBAR, 38),
                      get_line_color=rgb(AMBAR, 230), stroked=True,
                      line_width_min_pixels=1.5),
            pdk.Layer("ScatterplotLayer", puntos, get_position="[lon, lat]", get_radius=18,
                      radius_min_pixels=5, get_fill_color="rgb", get_line_color=blanco,
                      stroked=True, line_width_min_pixels=1, pickable=True),
            pdk.Layer("ScatterplotLayer", piloto, get_position="[lon, lat]", get_radius=30,
                      radius_min_pixels=9, get_fill_color=rgb(AMBAR), get_line_color=blanco,
                      stroked=True, line_width_min_pixels=2, pickable=True),
        ]
        vista = pdk.ViewState(latitude=TIENDA_PILOTO["lat"], longitude=TIENDA_PILOTO["lon"],
                              zoom=14.2)
        st.pydeck_chart(pdk.Deck(layers=capas, initial_view_state=vista, map_style=None,
                                 tooltip={"text": "{nombre}", "style": {
                                     "fontFamily": FUENTE, "fontSize": "13px",
                                     "backgroundColor": "#FFFFFF", "color": TINTA,
                                     "borderRadius": "8px", "padding": "6px 10px",
                                     "boxShadow": "0 8px 20px -8px rgba(41,52,98,.35)"}}),
                        height=ALTO_MAPA)
        if len(competencia):
            st.dataframe(competencia[["nombre", "giro", "distancia_m"]]
                         .rename(columns={"nombre": "Tienda", "giro": "Giro",
                                          "distancia_m": "Distancia (m)"}),
                         hide_index=True, use_container_width=True, height=220)
        st.caption("Fuente: © colaboradores de OpenStreetMap (ODbL). "
                   "Unión espacial con GeoPandas (EPSG:6372).")
    else:
        titulo_tarjeta("Tiendas alrededor de la tienda piloto")
        html('<div class="aviso">Aún no hay captura de OpenStreetMap: corre '
             "<code>python -m extractores.tiendas_osm</code> y luego "
             "<code>python -m pipeline.ejecutar</code>.</div>")

# --- IV. Clima y crédito --------------------------------------------------------------------
bloque("IV", "Clima y crédito")
col_clima, col_fiado = st.columns(2, gap="large")
with col_clima, st.container(border=True, key="tarjeta_clima"):
    titulo_tarjeta("Venta según el calor",
                   "Venta promedio por día según la temperatura máxima (Open-Meteo)"
                   '<span class="raya"></span>Promedio de todos los días')
    con_clima = diarias.dropna(subset=["temp_max_c"])
    tramos = list(TRAMOS_CALOR)
    calor = (con_clima.assign(tramo=pd.cut(con_clima["temp_max_c"], [-99, 29, 31, 33, 99],
                                           right=False, labels=tramos))
             .groupby("tramo", observed=True)["venta"].agg(promedio="mean", dias="count")
             .reset_index())
    if len(calor):
        general = con_clima["venta"].mean()
        # Diferencia de cada tramo contra el promedio de todos los días, ya como texto.
        calor["contra"] = (calor["promedio"] / general - 1) * 100
        calor["contra_txt"] = calor["contra"].map(lambda v: f"{v:+.1f} %")
        base = alt.Chart(calor).encode(
            x=alt.X("tramo:N", sort=tramos, title=None, axis=alt.Axis(labelAngle=0),
                    scale=alt.Scale(paddingInner=0.38)),
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
            "rgba(255,255,255,0.55)", "rgba(255,255,255,0)", vertical=True)).add_params(sel)
        promedio = alt.Chart(pd.DataFrame({"general": [general]})).mark_rule(
            color=TEXTO_EJE, strokeDash=[5, 4], strokeWidth=1.4).encode(
            y="general:Q", tooltip=[dinero("general", "Promedio de todos los días")])
        contra = base.mark_text(baseline="bottom", dy=-24, fontSize=11, fontWeight=700).encode(
            text="contra_txt:N",
            color=alt.condition(alt.datum.contra >= 0, alt.value("#08745A"),
                                alt.value("#B8285F")))
        st.altair_chart(estilo(barras + brillo + promedio + cifras(base, "promedio", True)
                               + contra, ALTO_FILA))
        alto, bajo = (calor.loc[calor["promedio"].idxmax()],
                      calor.loc[calor["promedio"].idxmin()])
        lectura(f"Los días de <b>{alto['tramo'][0].lower()}{alto['tramo'][1:]}</b> venden "
                f"<b>{(alto['promedio'] / bajo['promedio'] - 1) * 100:.1f} % más</b> que los "
                f"de <b>{bajo['tramo'][0].lower()}{bajo['tramo'][1:]}</b>")
    else:
        html('<div class="aviso">Aún no hay datos de clima.</div>')

with col_fiado, st.container(border=True, key="tarjeta_fiado"):
    titulo_tarjeta("Clientes con más fiado",
                   "Fiado acumulado desde 2025, sin descontar pagos · claves anónimas")
    if len(fiados):
        deudores = fiados.nlargest(8, "adeudo_bruto")
        st.altair_chart(estilo(barras_horizontales(
            deudores, "adeudo_bruto", "cliente_fiado",
            [alt.Tooltip("cliente_fiado:N", title="Cliente"),
             dinero("adeudo_bruto", "Fiado acumulado"),
             alt.Tooltip("compras:Q", title="Compras a fiado", format=",")],
            alt.value(degradado("#F7A8C4", "#EC6F9C", "#D6406E"))), ALTO_FILA))
        parte = deudores["adeudo_bruto"].sum() / fiados["adeudo_bruto"].sum() * 100
        lectura(f"Estos {len(deudores)} clientes suman <b>{pesos(deudores['adeudo_bruto'].sum())}"
                f"</b>, el <b>{parte:.0f} %</b> de todo el fiado")
    else:
        html('<div class="aviso">Aún no hay ventas a fiado registradas.</div>')

# --- Colofón ---------------------------------------------------------------------------------
html('<div class="pie"><span class="marca">AbarrotesPOS</span><br>'
     "Fuentes: punto de venta (demostración)<i></i>Open-Meteo<i></i>"
     "© colaboradores de OpenStreetMap<br>"
     "Linaje: cada cifra sale de data/oro y trae fuente, archivo de bronce y fecha de captura."
     "</div>")
