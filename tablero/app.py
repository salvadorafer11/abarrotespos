"""Tablero de AbarrotesPOS para el dueño de la tienda.  streamlit run tablero/app.py"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ORO = Path(__file__).resolve().parents[1] / "data" / "oro"
PLATA = Path(__file__).resolve().parents[1] / "data" / "plata"

st.set_page_config(page_title="AbarrotesPOS", layout="wide")
st.title("AbarrotesPOS · ¿Qué vende mi tienda y cuándo vende más?")

diarias = pd.read_csv(ORO / "ventas_diarias.csv", parse_dates=["fecha"])
producto = pd.read_csv(ORO / "ventas_producto_mes.csv")
if (diarias["fuente"] == "pos_demo").all():
    st.warning("Datos de DEMOSTRACIÓN (simulados). Se reemplazan por las ventas reales de la "
               "tienda piloto en cuanto el dueño las comparta.")

ultimo_mes = diarias["fecha"].max().to_period("M")
mes = diarias[diarias["fecha"].dt.to_period("M") == ultimo_mes]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Venta del mes", f"${mes['venta'].sum():,.0f}")
c2.metric("Ganancia del mes", f"${mes['ganancia'].sum():,.0f}")
c3.metric("Tickets del mes", f"{mes['tickets'].sum():,}")
c4.metric("Vendido a fiado", f"${mes['venta_fiado'].sum():,.0f}")

st.subheader("Venta por día")
st.line_chart(diarias.set_index("fecha")["venta"])

col1, col2 = st.columns(2)
with col1:
    st.subheader("Productos que más dejan (último mes)")
    top = producto[producto["mes"] == str(ultimo_mes)].nlargest(10, "ganancia")
    st.bar_chart(top.set_index("producto")["ganancia"])
with col2:
    st.subheader("Venta promedio por día de la semana")
    orden = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    st.bar_chart(diarias.groupby("dia_semana")["venta"].mean().reindex(orden))

st.subheader("Días con evento vs días normales")
st.dataframe(diarias.assign(evento=diarias["evento"].fillna("normal").replace("", "normal"))
             .groupby("evento")["venta"].agg(["mean", "count"]).round(0))

st.subheader("Competencia alrededor de la tienda (OpenStreetMap)")
tiendas_csv = PLATA / "tiendas_zona.csv"
competencia_csv = ORO / "competencia_tienda_piloto.csv"
tiendas = pd.read_csv(tiendas_csv) if tiendas_csv.exists() else pd.DataFrame()
competencia = pd.read_csv(competencia_csv) if competencia_csv.exists() else pd.DataFrame()
if len(tiendas):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from extractores.config import RADIO_COMPETENCIA_M, TIENDA_PILOTO

    cerca = set(competencia["osm_id"]) if len(competencia) else set()
    puntos = tiendas[["osm_id", "lat", "lon"]].assign(
        color=["#E8833A" if i in cerca else "#9AA0A6" for i in tiendas["osm_id"]], tam=25)
    piloto = pd.DataFrame({"osm_id": ["piloto"], "lat": [TIENDA_PILOTO["lat"]],
                           "lon": [TIENDA_PILOTO["lon"]], "color": ["#D62728"], "tam": [60]})
    st.map(pd.concat([puntos, piloto]), latitude="lat", longitude="lon", color="color",
           size="tam", zoom=14)
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Tiendas a menos de {RADIO_COMPETENCIA_M} m", len(competencia))
    m2.metric("Tiendas en Colima y Villa de Álvarez", len(tiendas))
    if len(competencia):
        m3.metric("La más cercana", f"{competencia['distancia_m'].min():,.0f} m")
        st.dataframe(competencia[["nombre", "giro", "distancia_m"]], hide_index=True)
    st.caption("🔴 tienda piloto · 🟠 competencia a menos de 500 m (unión espacial con "
               "GeoPandas, EPSG:6372) · ⚪ resto de la zona. "
               "Fuente: © colaboradores de OpenStreetMap (ODbL).")
    if not TIENDA_PILOTO["coordenadas_confirmadas"]:
        st.warning("Ubicación de la tienda piloto aproximada (centro de Villa de Álvarez).")
else:
    st.info("Aún no hay captura de OpenStreetMap: corre `python -m extractores.tiendas_osm` "
            "y luego `python -m pipeline.ejecutar`.")

st.caption("Linaje: cada cifra sale de data/oro y trae fuente, archivo de bronce y fecha de "
           "captura.")
