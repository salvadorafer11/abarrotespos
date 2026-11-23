"""Linaje (E2, tarea J5): rastrea una fila de oro hasta su archivo de bronce y su SHA-256.

    python -m pipeline.linaje data/oro/ventas_diarias.csv 0
    python -m pipeline.linaje data/oro/competencia_tienda_piloto.csv 0

Lee la fila, toma `fuente` y `archivo_bronce`, busca ese archivo en data/bronce/<fuente>/,
abre su .meta.json y vuelve a calcular el SHA-256 de los bytes originales (descomprimidos).
Si coincide con el del .meta.json, el dato no se altero desde que se capturo.
Solo usa la biblioteca estandar para que cualquiera lo pueda correr.
"""

import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def rastrear(archivo_oro, fila=0, raiz=RAIZ):
    archivo_oro = Path(archivo_oro)
    with open(raiz / archivo_oro if not archivo_oro.is_absolute() else archivo_oro,
              encoding="utf-8", newline="") as f:
        registro = next(r for i, r in enumerate(csv.DictReader(f)) if i == fila)
    fuente, nombre = registro["fuente"], registro["archivo_bronce"]
    ruta = next((raiz / "data" / "bronce" / fuente).rglob(nombre))
    meta = json.loads((ruta.parent / f"{nombre.split('.')[0]}.meta.json")
                      .read_text(encoding="utf-8"))
    with gzip.open(ruta, "rb") as g:
        sha = hashlib.sha256(g.read()).hexdigest()
    return {
        "tabla": f"{archivo_oro.as_posix()} (fila {fila})",
        "fuente": fuente,
        "capturado_utc_en_tabla": registro["capturado_utc"],
        "bronce": ruta.relative_to(raiz).as_posix(),
        "capturado_utc_en_meta": meta["capturado_utc"],
        "sha256_meta": meta["sha256"],
        "sha256_recalculado": sha,
        "integro": sha == meta["sha256"]
        and registro["capturado_utc"] == meta["capturado_utc"],
    }


def main():
    archivo = sys.argv[1] if len(sys.argv) > 1 else "data/oro/ventas_diarias.csv"
    fila = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    resultado = rastrear(archivo, fila)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if not resultado["integro"]:
        raise SystemExit("LINAJE ROTO: el SHA-256 o la fecha no coinciden")


if __name__ == "__main__":
    main()
