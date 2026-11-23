"""Union espacial (E2, tarea J2): competencia a 500 m de la tienda piloto con GeoPandas.

Los puntos llegan en grados (EPSG:4326). Para que el radio de 500 m sea de metros reales
se proyectan a EPSG:6372 (Mexico ITRF2008 / LCC, unidades en metros), se traza un buffer
alrededor de la tienda piloto y se hace un `sjoin` con predicado `within`.

    python -m pipeline.ejecutar   # escribe data/oro/competencia_tienda_piloto.csv
"""

import geopandas as gpd
import pandas as pd

from extractores import config

CRS_GRADOS = "EPSG:4326"
CRS_METROS = "EPSG:6372"
COLUMNAS = [
    "osm_id", "nombre", "giro", "lat", "lon", "distancia_m", "radio_m", "tienda_piloto",
    "coordenadas_piloto_confirmadas", "fuente", "archivo_bronce", "capturado_utc",
]


def _puntos(df, lon="lon", lat="lat"):
    geom = gpd.points_from_xy(df[lon], df[lat])
    return gpd.GeoDataFrame(df.copy(), geometry=geom, crs=CRS_GRADOS).to_crs(CRS_METROS)


def competencia(tiendas, piloto=None, radio_m=None):
    """Tiendas OSM dentro del radio de la piloto, ordenadas de la mas cercana a la mas lejana.

    La propia tienda piloto se excluye si aparece mapeada en OSM con su nombre.
    """
    piloto = piloto or config.TIENDA_PILOTO
    radio_m = radio_m or config.RADIO_COMPETENCIA_M
    if tiendas is None or tiendas.empty:
        return pd.DataFrame(columns=COLUMNAS)

    tiendas = tiendas[~tiendas["nombre"].str.contains("amiguito", case=False, na=False)]
    puntos = _puntos(tiendas)
    centro = _puntos(pd.DataFrame({"tienda_piloto": [piloto["nombre"]],
                                   "lat": [piloto["lat"]], "lon": [piloto["lon"]]}))
    zona = centro[["tienda_piloto"]].set_geometry(centro.buffer(radio_m), crs=CRS_METROS)

    dentro = gpd.sjoin(puntos, zona, how="inner", predicate="within")
    dentro["distancia_m"] = dentro.distance(centro.geometry.iloc[0]).round(1)
    dentro["radio_m"] = radio_m
    dentro["coordenadas_piloto_confirmadas"] = bool(piloto["coordenadas_confirmadas"])
    salida = pd.DataFrame(dentro.drop(columns=["geometry", "index_right"]))
    return salida[COLUMNAS].sort_values("distancia_m").reset_index(drop=True)
