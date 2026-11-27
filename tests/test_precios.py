"""Pruebas sin red de los precios de mercado (PROFECO QQP): extractor y comparación."""

import io

import pandas as pd

from extractores import precios_profeco as pp
from pipeline import precios

ZONAS = [("Colima", "Colima", ["Colima", "Villa de Álvarez"]),
         ("Guadalajara", "Jalisco", ["Guadalajara", "Zapopan"])]


def test_portal_toma_el_anio_mas_reciente():
    pagina = ('<a href="docs/qqp/2024.rar">2024</a> <a href="docs/qqp/2026.rar">2026</a>'
              '<a href="docs/qqp/2025.rar">2025</a> <a href="docs/otro.csv">x</a>')
    assert pp.enlace_mas_reciente(pagina, "https://datos.profeco.gob.mx/index.php") == (
        "https://datos.profeco.gob.mx/docs/qqp/2026.rar")


def test_rar_toma_las_quincenas_del_ultimo_mes():
    miembros = ["2026/09-2026_Q2.csv", "2026/10-2026_Q2.csv", "2026/10-2026_Q1.csv",
                "2026/leeme.txt"]
    assert pp.mes_mas_reciente(miembros) == ("2026-10", ["2026/10-2026_Q1.csv",
                                                         "2026/10-2026_Q2.csv"])


def test_zona_usa_colima_y_si_no_hay_la_mas_cercana():
    csv = ("producto,precio,estado,municipio\n"
           "Leche,30,Jalisco,Guadalajara\nLeche,31,Jalisco,Tepatitlán\n")
    por_zona = pp.filas_de_zona(io.StringIO(csv), ZONAS)
    assert len(por_zona["Guadalajara"]) == 1 and por_zona["Colima"] == []
    assert pp.elegir_zona(por_zona, ZONAS)[0] == "Guadalajara"
    por_zona["Colima"] = [{"producto": "Leche"}]
    assert pp.elegir_zona(por_zona, ZONAS)[0] == "Colima"


def test_cantidad_lleva_todo_a_ml_o_g():
    assert precios.cantidad("Paquete con 12 Latas de 355 Ml.", "ml") == 12 * 355
    assert precios.cantidad("Paquete con 12 Latas de 355 Ml.", "ml", por_pieza=True) == 355
    assert precios.cantidad("Bolsa Plástico 2 Kg. Estándar", "g") == 2000
    assert precios.cantidad("Botella 2.5 Lt. No Retornable", "ml") == 2500
    assert precios.cantidad("Lata 140 Gr.", "ml") is None  # unidad equivocada
    assert precios.cantidad("Concha. Pieza", "pieza") == 1


def _fila(producto, presentacion, marca, precio, tienda, cadena="Wal-mart",
          giro="Supermercado / Tienda de Autoservicio"):
    return {"producto": producto, "presentacion": presentacion, "marca": marca,
            "precio": precio, "fecha_registro": "2026/10/16", "cadena_comercial": cadena,
            "giro": giro, "nombre_comercial": tienda, "municipio": "Guadalajara",
            "latitud": 20.6, "longitud": -103.3, "zona": "Guadalajara",
            "fuente": "profeco_qqp", "archivo_bronce": "qqp.csv.gz", "capturado_utc": "t"}


def _crudo():
    return pd.DataFrame([
        _fila("Leche Ultrapasteurizada", "Caja 1 Lt. Entera", "Lala", 30, "A"),
        _fila("Leche Ultrapasteurizada", "Caja 1 Lt. Entera", "Great Value", 20, "B"),
        _fila("Leche Ultrapasteurizada", "Caja 1 Lt. Entera", "Alpura", 28, "C", "Chedraui"),
        _fila("Leche Ultrapasteurizada", "Caja 1 Lt. Entera", "Santa Clara", 32, "D", "Oxxo"),
        # Fuera: giro que no vende abarrotes y precio atípico (error de captura).
        _fila("Leche Ultrapasteurizada", "Caja 1 Lt. Entera", "Lala", 25, "F", "Farmacia",
              "Farmacias"),
        _fila("Leche Ultrapasteurizada", "Caja 1 Lt. Entera", "Lala", 300, "E"),
        # Fuera: tamaño muy distinto (garrafón) aunque sea agua natural.
        _fila("Agua Sin Gas", "Garrafón 20 Lt.", "Ciel", 50, "A"),
    ])


def test_plata_filtra_giros_atipicos_y_marca_propia():
    p = precios.plata(_crudo())
    leche = p[p["producto_tienda"] == "Leche entera 1 L"]
    assert sorted(leche["nombre_comercial"]) == ["A", "B", "C", "D"]
    assert leche.set_index("marca")["marca_propia"].to_dict() == {
        "Lala": False, "Great Value": True, "Alpura": False, "Santa Clara": False}
    assert "Agua natural 1 L" not in set(p["producto_tienda"])


def test_oro_compara_precio_y_costo_con_linaje():
    ventas = pd.DataFrame({
        "fecha": pd.to_datetime(["2026-11-01", "2026-11-02"]), "producto": ["Leche entera 1 L"] * 2,
        "categoria": ["lacteos"] * 2, "piezas": [10, 20], "precio_unitario": [29.0, 29.0],
        "costo_unitario": [29.0, 29.0]})
    comparativo, cadenas = precios.oro(precios.plata(_crudo()), ventas)
    fila = comparativo.iloc[0]
    assert fila["mercado_mediana"] == 29.0  # mediana de 20, 28, 30 y 32
    assert fila["mejor_marca"] == "Great Value" and fila["mejor_marca_propia"]
    # El ahorro se mide con la marca comercial más barata (Alpura a $28), no la marca propia.
    assert fila["comercial_marca"] == "Alpura" and fila["ahorro_por_pieza"] == 1.0
    assert fila["ahorro_mes"] == 30.0
    assert {"fuente", "archivo_bronce", "capturado_utc"} <= set(comparativo.columns)
    assert {"fuente", "archivo_bronce", "capturado_utc"} <= set(cadenas.columns)
    assert cadenas.iloc[0]["cadena_comercial"] == "Wal-mart"  # 20 y 30: 86 % de la mediana


def test_sin_captura_no_truena():
    vacio = precios.plata(pd.DataFrame())
    assert list(vacio.columns) == precios.COLUMNAS_PLATA
    ventas = pd.DataFrame({"fecha": pd.to_datetime(["2026-11-01"]), "producto": ["X"],
                           "categoria": ["c"], "piezas": [1], "precio_unitario": [2.0],
                           "costo_unitario": [1.0]})
    comparativo, cadenas = precios.oro(vacio, ventas)
    assert len(comparativo) == 1 and cadenas.empty
