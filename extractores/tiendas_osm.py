"""Fuente especializada E2 (geoespacial): comercios de abarrotes en Colima desde OpenStreetMap.

Se consulta la API Overpass (sin llave, datos ODbL). Solo se guardan atributos del
NEGOCIO (giro, nombre comercial, coordenadas). OSM no trae datos de personas fisicas;
si una etiqueta trajera telefono, correo o sitio web de una persona, se elimina aqui,
antes de escribir en bronce (regla de cero datos personales).

Uso:  python -m extractores.tiendas_osm
"""

import json

from extractores import bronce, config
from extractores.base import ExtractorEtico

# Etiquetas de contacto que nunca se guardan, aunque OSM las traiga.
ETIQUETAS_PROHIBIDAS = {"phone", "contact:phone", "email", "contact:email", "contact:whatsapp",
                        "contact:facebook", "contact:instagram", "website", "operator:phone"}


def consulta_overpass(bbox=config.BBOX_ZONA, giros=config.OSM_GIROS):
    s, o, n, e = bbox
    filtros = "".join(f'nwr["shop"="{g}"]({s},{o},{n},{e});' for g in giros)
    return f"[out:json][timeout:60];({filtros});out center tags;"


def sin_datos_personales(elementos):
    limpios = []
    for el in elementos:
        tags = {k: v for k, v in el.get("tags", {}).items() if k not in ETIQUETAS_PROHIBIDAS}
        limpios.append({**el, "tags": tags})
    return limpios


def capturar(extractor=None):
    ex = extractor or ExtractorEtico(pausa=2.0, timeout=90)
    q = consulta_overpass()
    r = ex.get(config.OVERPASS_URL, params={"data": q})
    datos = r.json()
    datos["elements"] = sin_datos_personales(datos.get("elements", []))
    contenido = json.dumps(datos, ensure_ascii=False).encode("utf-8")
    hoy = bronce.ahora_utc().date().isoformat()
    ruta = bronce.guardar(
        "osm_overpass",
        contenido,
        {"url": config.OVERPASS_URL, "consulta": q, "licencia": "ODbL 1.0 (OpenStreetMap)",
         "nota": "etiquetas de contacto eliminadas antes de guardar",
         "terminos": config.APIS_CON_TERMINOS["overpass-api.de"]},
        subruta=hoy[:7],
        nombre=f"tiendas_{hoy}",
    )
    return ruta, len(datos["elements"])


def main():
    inicio = bronce.ahora_utc()
    fila = {"ejecucion_id": bronce.id_ejecucion(), "disparador": bronce.disparador(),
            "fuente": "osm_overpass", "inicio_utc": inicio.isoformat()}
    try:
        ruta, n = capturar()
        fila.update(estado="success", registros=n, mensaje=ruta.name)
    except Exception as e:
        fila.update(estado="failure", registros=0, mensaje=str(e)[:300])
    fin = bronce.ahora_utc()
    fila.update(fin_utc=fin.isoformat(), duracion_s=round((fin - inicio).total_seconds(), 2))
    bronce.registrar(fila)
    print(json.dumps(fila, ensure_ascii=False))


if __name__ == "__main__":
    main()
