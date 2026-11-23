"""Pipeline completo: bronce -> puerta de calidad -> plata -> oro (con linaje).

    python -m pipeline.ejecutar

Cada fila de oro conserva `fuente`, `archivo_bronce` y `capturado_utc`: con eso cualquier
cifra del tablero se rastrea hasta el archivo crudo y su SHA-256 (ver *.meta.json).
"""

import gzip
import io
import json
import math
from pathlib import Path

import pandas as pd

try:  # pandera >= 0.24
    import pandera.pandas as pa
except ImportError:
    import pandera as pa

from extractores import bronce, config
from pipeline import ventas_demo

ESQUEMA_VENTAS = pa.DataFrameSchema(
    {
        "ticket": pa.Column(str, pa.Check.str_matches(r"^T\d{7}$", error="ticket_formato")),
        "fecha": pa.Column("datetime64[ns]", coerce=True),
        "hora": pa.Column(int, pa.Check.in_range(6, 23, error="hora_fuera_de_horario")),
        "producto": pa.Column(str, pa.Check.str_length(min_value=2)),
        "categoria": pa.Column(str),
        "piezas": pa.Column(int, pa.Check.in_range(1, 50, error="piezas_fuera_de_rango")),
        "precio_unitario": pa.Column(float, pa.Check.in_range(0.5, 2000, error="precio_rango")),
        "costo_unitario": pa.Column(float, pa.Check.gt(0, error="costo_no_positivo")),
        "forma_pago": pa.Column(str, pa.Check.isin(["contado", "fiado"], error="forma_pago")),
        "cliente_fiado": pa.Column(str, nullable=True),
        "evento": pa.Column(str, nullable=True),
        "fuente": pa.Column(str, pa.Check.isin(["pos_demo", "pos_cliente"])),
        "archivo_bronce": pa.Column(str),
        "capturado_utc": pa.Column(str),
    },
    checks=[pa.Check(lambda d: d["precio_unitario"] >= d["costo_unitario"],
                     element_wise=False, error="vende_abajo_del_costo")],
    strict=True,
)


def _ultimo(fuente, patron):
    archivos = sorted((config.DIR_BRONCE / fuente).rglob(patron))
    return archivos[-1] if archivos else None


def _meta(ruta):
    nombre = ruta.name.split(".")[0]
    return json.loads((ruta.parent / f"{nombre}.meta.json").read_text(encoding="utf-8"))


def ventas_a_bronce(clima=None):
    """Genera la demo y la guarda en bronce (si ya existe la misma, no se duplica)."""
    df = ventas_demo.generar(clima=clima)
    contenido = df.to_csv(index=False).encode("utf-8")
    return bronce.guardar("pos_demo", contenido, {"descripcion": "tickets sinteticos semilla 42",
                                                  "generador": "pipeline/ventas_demo.py"},
                          subruta="demo", nombre="tickets_demo", ext="csv")


def validar(df, esquema):
    try:
        return esquema.validate(df, lazy=True), df.iloc[0:0].assign(motivo="")
    except pa.errors.SchemaErrors as e:
        casos = e.failure_cases.dropna(subset=["index"])
        motivos = (casos.assign(r=casos["column"].astype(str) + ": " + casos["check"].astype(str))
                   .groupby("index")["r"].agg(lambda r: " | ".join(sorted(set(r)))))
        idx = motivos.index.astype(int)
        return df.drop(index=idx), df.loc[idx].assign(motivo=motivos.to_numpy())


def plata_ventas(ruta):
    with gzip.open(ruta, "rb") as f:
        df = pd.read_csv(io.BytesIO(f.read()), dtype={"cliente_fiado": str, "evento": str})
    df[["cliente_fiado", "evento"]] = df[["cliente_fiado", "evento"]].fillna("")
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["archivo_bronce"] = ruta.name
    df["capturado_utc"] = _meta(ruta)["capturado_utc"]
    return validar(df, ESQUEMA_VENTAS)


def plata_clima():
    ruta = _ultimo("open_meteo", "*.json.gz")
    if not ruta:
        return pd.DataFrame(columns=["fecha", "temp_max_c", "temp_min_c", "lluvia_mm"])
    d = json.loads(gzip.open(ruta).read())["daily"]
    return pd.DataFrame({
        "fecha": pd.to_datetime(d["time"]), "temp_max_c": d["temperature_2m_max"],
        "temp_min_c": d["temperature_2m_min"], "lluvia_mm": d["precipitation_sum"],
        "fuente": "open_meteo", "archivo_bronce": ruta.name,
        "capturado_utc": _meta(ruta)["capturado_utc"],
    })


def _distancia_m(lat1, lon1, lat2, lon2):
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def plata_tiendas():
    ruta = _ultimo("osm_overpass", "*.json.gz")
    if not ruta:
        return pd.DataFrame(columns=["osm_id", "nombre", "giro", "lat", "lon"])
    elementos = json.loads(gzip.open(ruta).read())["elements"]
    filas = []
    for el in elementos:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None:
            continue
        t = el.get("tags", {})
        filas.append({"osm_id": f"{el['type']}/{el['id']}", "nombre": t.get("name", "(sin nombre)"),
                      "giro": t.get("shop", ""), "lat": lat, "lon": lon})
    df = pd.DataFrame(filas).drop_duplicates("osm_id")
    tp = config.TIENDA_PILOTO
    df["distancia_piloto_m"] = [round(_distancia_m(tp["lat"], tp["lon"], a, b))
                                for a, b in zip(df["lat"], df["lon"], strict=True)]
    df["competencia_directa"] = df["distancia_piloto_m"] <= config.RADIO_COMPETENCIA_M
    return df.assign(fuente="osm_overpass", archivo_bronce=ruta.name,
                     capturado_utc=_meta(ruta)["capturado_utc"])


def oro(ventas, clima):
    v = ventas.assign(importe=ventas["piezas"] * ventas["precio_unitario"],
                      ganancia=ventas["piezas"] * (ventas["precio_unitario"]
                                                   - ventas["costo_unitario"]))
    linaje = ["fuente", "archivo_bronce", "capturado_utc"]
    diarias = (v.groupby(["fecha", "evento", *linaje], as_index=False)
               .agg(tickets=("ticket", "nunique"), piezas=("piezas", "sum"),
                    venta=("importe", "sum"), ganancia=("ganancia", "sum"),
                    venta_fiado=("importe", lambda s: s[v.loc[s.index, "forma_pago"] == "fiado"]
                                 .sum())))
    diarias["dia_semana"] = diarias["fecha"].dt.day_name()
    if len(clima):
        diarias = diarias.merge(clima[["fecha", "temp_max_c", "lluvia_mm"]], on="fecha",
                                how="left")
    producto_mes = (v.assign(mes=v["fecha"].dt.to_period("M").astype(str))
                    .groupby(["mes", "producto", "categoria", *linaje], as_index=False)
                    .agg(piezas=("piezas", "sum"), venta=("importe", "sum"),
                         ganancia=("ganancia", "sum")))
    fiados = (v[v["forma_pago"] == "fiado"].groupby(["cliente_fiado", *linaje], as_index=False)
              .agg(compras=("ticket", "nunique"), adeudo_bruto=("importe", "sum")))
    return {"ventas_diarias": diarias, "ventas_producto_mes": producto_mes,
            "fiados_por_cliente": fiados}


def main(base=None):
    base = Path(base) if base else config.RAIZ / "data"
    for d in ("plata", "oro", "cuarentena"):
        (base / d).mkdir(parents=True, exist_ok=True)
    clima = plata_clima()
    # Prioridad: ventas reales del cliente > demo ya capturada > generar la demo una vez.
    ruta = (_ultimo("pos_cliente", "*.csv.gz") or _ultimo("pos_demo", "*.csv.gz")
            or ventas_a_bronce(clima))
    ventas, rechazados = plata_ventas(ruta)
    tiendas = plata_tiendas()
    ventas.to_csv(base / "plata" / "ventas.csv", index=False)
    clima.to_csv(base / "plata" / "clima_diario.csv", index=False)
    tiendas.to_csv(base / "plata" / "tiendas_zona.csv", index=False)
    rechazados.to_csv(base / "cuarentena" / "ventas.csv", index=False)
    for nombre, tabla in oro(ventas, clima).items():
        tabla.to_csv(base / "oro" / f"{nombre}.csv", index=False)
    reporte = {"ventas_en_plata": len(ventas), "ventas_en_cuarentena": len(rechazados),
               "dias_de_clima": len(clima), "tiendas_osm": len(tiendas),
               "fuente_ventas": ruta.parent.parent.name}
    (config.DIR_CALIDAD / "reporte-puerta.json").write_text(json.dumps(reporte, indent=2))
    print(json.dumps(reporte, ensure_ascii=False))
    if len(ventas) == 0:
        raise SystemExit("Puerta de calidad: plata vacia")
    return reporte


if __name__ == "__main__":
    main()
