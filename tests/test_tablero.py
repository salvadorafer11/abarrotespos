"""Prueba de humo del tablero: cada vista se abre sin errores (sin navegador, con AppTest).

Corre tablero/app.py con los datos de data/oro y data/plata del repositorio, igual que lo ve
el dueño. Si una vista truena (un import roto, una columna que ya no existe), el CI se pone en
rojo antes de unir el cambio.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "tablero" / "app.py")
VISTAS = ["inicio", "informe", "venta", "productos", "precios", "competencia", "clima"]


def abrir(vista, **extra):
    at = AppTest.from_file(APP, default_timeout=120)
    at.query_params["vista"] = vista
    for clave, valor in extra.items():
        at.query_params[clave] = valor
    return at.run()


def texto(at):
    return " ".join(m.value for m in at.markdown)


@pytest.mark.parametrize("vista", VISTAS)
def test_cada_vista_abre_sin_errores(vista):
    at = abrir(vista)
    assert not at.exception, at.exception
    assert "app-barra" in texto(at)  # la barra superior siempre se dibuja


def test_buscador_de_precios_encuentra_con_errores_de_dedo():
    at = abrir("precios")
    at.text_input(key="buscar_precio").set_value("asucar").run()
    assert not at.exception, at.exception
    assert "Quisiste decir <b>Azúcar estándar 1 kg</b>" in texto(at)
    assert "Mostrando 1 de" in texto(at)  # la tabla queda filtrada


def test_buscador_toma_la_busqueda_del_enlace():
    at = abrir("precios", q="chesco")
    assert not at.exception, at.exception
    assert "Refresco de cola" in texto(at)
