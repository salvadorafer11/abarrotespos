"""Clima diario de Colima desde Open-Meteo (API sin llave, licencia CC BY 4.0).

Sirve para explicar ventas: dias de calor venden mas refresco y hielo; dias de lluvia,
menos clientes. Uso:  python -m extractores.clima [--desde 2025-01-01]
"""

import argparse
import json
from datetime import date, timedelta

from extractores import bronce, config
from extractores.base import ExtractorEtico


def capturar(desde=config.CLIMA_DESDE, hasta=None, extractor=None):
    # El archivo historico de Open-Meteo llega con unos dias de retraso.
    hasta = hasta or (date.today() - timedelta(days=5)).isoformat()
    ex = extractor or ExtractorEtico()
    params = {
        "latitude": config.TIENDA_PILOTO["lat"],
        "longitude": config.TIENDA_PILOTO["lon"],
        "start_date": desde,
        "end_date": hasta,
        "daily": config.OPEN_METEO_VARIABLES,
        "timezone": config.ZONA_HORARIA,
    }
    r = ex.get(config.OPEN_METEO_ARCHIVO, params=params)
    datos = r.json()
    if datos.get("error"):
        raise RuntimeError(f"Open-Meteo respondio error: {datos.get('reason')}")
    ruta = bronce.guardar(
        "open_meteo",
        r.content,
        {"url": config.OPEN_METEO_ARCHIVO, "params": params, "licencia": "CC BY 4.0"},
        subruta=hasta[:7],
        nombre=f"clima_{desde}_{hasta}",
    )
    return ruta, len(datos.get("daily", {}).get("time", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default=config.CLIMA_DESDE)
    a = ap.parse_args()
    inicio = bronce.ahora_utc()
    fila = {"ejecucion_id": bronce.id_ejecucion(), "disparador": bronce.disparador(),
            "fuente": "open_meteo", "inicio_utc": inicio.isoformat()}
    try:
        ruta, n = capturar(a.desde)
        fila.update(estado="success", registros=n, mensaje=ruta.name)
    except Exception as e:  # toda falla queda en la bitacora (insumo de MTBF/MTTR)
        fila.update(estado="failure", registros=0, mensaje=str(e)[:300])
    fin = bronce.ahora_utc()
    fila.update(fin_utc=fin.isoformat(), duracion_s=round((fin - inicio).total_seconds(), 2))
    bronce.registrar(fila)
    print(json.dumps(fila, ensure_ascii=False))


if __name__ == "__main__":
    main()
