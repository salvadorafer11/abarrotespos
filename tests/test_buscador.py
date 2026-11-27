"""Pruebas del buscador de productos (búsqueda léxica que tolera errores de dedo)."""

import pytest

from tablero import buscador as b
from tablero.productos import PRODUCTOS

DOCS = [b.documento(clave, nombre) for clave, (nombre, _, _) in PRODUCTOS.items()]


def primero(consulta, docs=DOCS):
    resultados = b.buscar(consulta, docs)
    return resultados[0][0] if resultados else None


def test_normaliza_acentos_y_signos():
    assert b.normalizar("  Azúcar ESTÁNDAR, 1 kg ") == "azucar estandar 1 kg"
    assert b.palabras("papel de baño") == ["papel", "bano"]


def test_distancia_cuenta_intercambios_como_un_error():
    assert b.distancia("lehce", "leche") == 1
    assert b.distancia("asucar", "azucar") == 1
    assert b.distancia("", "pan") == 3


@pytest.mark.parametrize("consulta, esperado", [
    ("asucar", "Azucar estandar 1 kg"),        # z por s
    ("lehce", "Leche entera 1 L"),             # letras intercambiadas
    ("tortiya", "Tortilla de maiz 1 kg"),      # ll por y
    ("jabon", "Jabon de lavanderia 1 kg"),     # sin acento
    ("blankeador", "Cloro 1 L"),               # sinónimo con error
    ("papel de baño", "Papel higienico 4 rollos"),
    ("atún", "Atun en lata 140 g"),
    ("azu", "Azucar estandar 1 kg"),           # mientras se escribe
    ("cerbesa", "Cerveza lata 355 ml"),        # dos errores en 7 letras
    ("jugo naranja", "Jugo 1 L"),
])
def test_encuentra_aunque_haya_errores(consulta, esperado):
    assert primero(consulta) == esperado


def test_nombres_comunes_traen_todos_los_que_aplican():
    claves = {c for c, _ in b.buscar("chesco", DOCS)}
    assert claves == {"Refresco cola 600 ml", "Refresco cola 2.5 L"}
    assert primero("refresco 600") == "Refresco cola 600 ml"
    # Lo que solo se parece de lejos no sale si hay uno mucho mejor.
    assert {c for c, _ in b.buscar("pan", DOCS)} == {"Pan de caja grande", "Pan dulce pieza"}


def test_marcas_de_profeco_tambien_cuentan():
    docs = [b.documento("Leche entera 1 L", "Leche entera 1 L", marcas=["Sello Rojo"]),
            b.documento("Arroz 1 kg", "Arroz 1 kg")]
    assert primero("sello rojo", docs) == "Leche entera 1 L"


def test_quisiste_decir_solo_con_errores_de_dedo():
    azucar = b.documento("Azucar estandar 1 kg", "Azúcar estándar 1 kg")
    refresco = b.documento("Refresco cola 600 ml", "Refresco de cola 600 ml")
    assert b.hubo_correccion("asucar", azucar)
    assert not b.hubo_correccion("azúcar", azucar)
    assert not b.hubo_correccion("azu", azucar)        # todavía escribiendo
    assert not b.hubo_correccion("chesco", refresco)   # sinónimo bien escrito


def test_sin_coincidencias_no_inventa():
    assert b.buscar("xyzw", DOCS) == []
    assert b.buscar("  ", DOCS) == []
    assert b.buscar("de la", DOCS) == []
