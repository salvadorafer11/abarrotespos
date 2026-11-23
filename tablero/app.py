"""Tablero de AbarrotesPOS para el dueño de la tienda.  streamlit run tablero/app.py"""

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

tiendas_csv = PLATA / "tiendas_zona.csv"
if tiendas_csv.exists():
    tiendas = pd.read_csv(tiendas_csv)
    if len(tiendas):
        st.subheader("Competencia alrededor de la tienda (OpenStreetMap)")
        st.map(tiendas, latitude="lat", longitude="lon")
        st.caption(f"{int(tiendas['competencia_directa'].sum())} tiendas a menos de 500 m. "
                   "Fuente: © colaboradores de OpenStreetMap (ODbL).")

st.caption("Linaje: cada cifra sale de data/oro y trae fuente, archivo de bronce y fecha de "
           "captura.")
