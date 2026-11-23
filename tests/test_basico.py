"""Pruebas sin red: demo de ventas, puerta de calidad, linaje, geo y diseño experimental."""

import pandas as pd

from extractores import tiendas_osm
from laboratorio import experimento_factorial as ef
from pipeline import ejecutar, geo, ventas_demo


def test_demo_reproducible_y_sin_nombres():
    a = ventas_demo.generar("2025-01-01", "2025-01-10")
    b = ventas_demo.generar("2025-01-01", "2025-01-10")
    pd.testing.assert_frame_equal(a, b)
    fiado = a[a["forma_pago"] == "fiado"]["cliente_fiado"]
    assert fiado.str.match(r"^F\d{3}$").all()  # claves anonimas, nunca nombres
    assert (a["fuente"] == "pos_demo").all()


def test_puerta_manda_a_cuarentena_lo_que_rompe_reglas():
    df = ventas_demo.generar("2025-01-01", "2025-01-02")
    df[["cliente_fiado", "evento"]] = df[["cliente_fiado", "evento"]].fillna("")
    df = df.assign(archivo_bronce="x.csv.gz", capturado_utc="2026-11-23T00:00:00+00:00")
    df.loc[0, "piezas"] = 999
    df.loc[1, "precio_unitario"] = 0.1
    buenos, malos = ejecutar.validar(df, ejecutar.ESQUEMA_VENTAS)
    assert len(malos) == 2 and len(buenos) == len(df) - 2
    assert malos["motivo"].str.len().gt(0).all()


def test_oro_conserva_linaje():
    df = ventas_demo.generar("2025-01-01", "2025-01-05")
    df[["cliente_fiado", "evento"]] = df[["cliente_fiado", "evento"]].fillna("")
    df = df.assign(archivo_bronce="x.csv.gz", capturado_utc="t")
    for tabla in ejecutar.oro(df, pd.DataFrame()).values():
        assert {"fuente", "archivo_bronce", "capturado_utc"} <= set(tabla.columns)


def test_osm_quita_contactos():
    el = [{"type": "node", "id": 1, "tags": {"shop": "convenience", "phone": "312", "name": "X"}}]
    limpio = tiendas_osm.sin_datos_personales(el)[0]["tags"]
    assert "phone" not in limpio and limpio["name"] == "X"


def test_distancia_haversine():
    assert abs(ejecutar._distancia_m(19.0, -103.0, 19.0045, -103.0) - 500) < 5


def test_fraccionado_tiene_alias_d_igual_abc():
    p = ef.plan_2k(list("ABCD"), 1, generador=("D", "ABC"))
    assert len(p) == 8
    assert (p["D"] == p["A"] * p["B"] * p["C"]).all()
    assert len(ef.plan_2k(list("ABC"), 2)) == 16


def test_geo_sjoin_500m_en_metros():
    piloto = {"nombre": "piloto", "lat": 19.2675, "lon": -103.7375,
              "coordenadas_confirmadas": True}
    tiendas = pd.DataFrame({
        "osm_id": ["node/1", "node/2", "node/3"],
        "nombre": ["Cerca", "Lejos", "Abarrotes El Amiguito"],
        "giro": ["convenience"] * 3,
        "lat": [19.2675 + 0.0027, 19.2675 + 0.0063, 19.2675],  # ~300 m y ~700 m al norte
        "lon": [-103.7375] * 3,
        "fuente": "osm_overpass", "archivo_bronce": "x.json.gz", "capturado_utc": "t",
    })
    c = geo.competencia(tiendas, piloto, 500)
    assert list(c["osm_id"]) == ["node/1"]  # la piloto misma no cuenta como competencia
    esperado = ejecutar._distancia_m(19.2675, -103.7375, 19.2675 + 0.0027, -103.7375)
    assert abs(c["distancia_m"].iloc[0] - esperado) < 5
    assert {"fuente", "archivo_bronce", "capturado_utc"} <= set(c.columns)


def test_geo_sin_tiendas_no_truena():
    vacio = pd.DataFrame(columns=["osm_id", "nombre", "giro", "lat", "lon"])
    assert list(geo.competencia(vacio).columns) == geo.COLUMNAS


def test_linaje_rastrea_oro_hasta_bronce(tmp_path):
    import json

    from extractores import bronce
    from pipeline import linaje

    ruta = bronce.guardar("pos_demo", b"a,b\n1,2\n", {"capturado_utc": "t0"}, subruta="demo",
                          nombre="x", base=tmp_path / "data" / "bronce", ext="csv")
    encabezado = "fuente,archivo_bronce,capturado_utc"
    (tmp_path / "oro.csv").write_text(f"{encabezado}\npos_demo,{ruta.name},t0\n")
    r = linaje.rastrear("oro.csv", 0, raiz=tmp_path)
    assert r["integro"] and r["sha256_meta"] == r["sha256_recalculado"]
    meta = ruta.parent / "x.meta.json"
    meta.write_text(json.dumps({**json.loads(meta.read_text()), "sha256": "0" * 64}))
    assert not linaje.rastrear("oro.csv", 0, raiz=tmp_path)["integro"]
