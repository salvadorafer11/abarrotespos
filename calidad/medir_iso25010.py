"""Mediciones ISO/IEC 25010 de AbarrotesPOS que se calculan con Python (solo lectura).

    python calidad/medir_iso25010.py --confirmacion laboratorio/resultados/confirmacion.csv \
        --salida calidad/mediciones/iso25010.json

Las demas mediciones (ruff, pytest, radon, pip-audit) se guardan como texto en
calidad/mediciones/ con los comandos indicados en docs/calidad/iso25010.md.
Autor: Jose Rey Sanchez Navarro (Calidad, E2), con asistencia de IA (Claude Code).
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
TABLAS_ORO = ["ventas_diarias", "ventas_producto_mes", "fiados_por_cliente"]


def adecuacion_funcional(raiz):
    """Filas de la ficha de entrega cuyo estado dice 'hecho' sin 'falta' ni 'pendiente'."""
    filas = []
    for linea in (raiz / "docs" / "E2" / "ENTREGA.md").read_text(encoding="utf-8").splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) == 5 and celdas[0] not in ("Materia", "") and not set(celdas[0]) <= {"-"}:
            filas.append({"materia": celdas[0], "criterio": celdas[1], "estado": celdas[4]})
    hechas = [f for f in filas if re.search(r"\bhecho\b", f["estado"], re.I)
              and not re.search(r"falta|pendiente", f["estado"], re.I)]
    return {"criterios": len(filas), "hechos": len(hechas),
            "pct_hechos": round(100 * len(hechas) / len(filas), 2) if filas else None,
            "estados": [f["estado"] for f in filas]}


def desempeno(ruta):
    if not ruta or not Path(ruta).exists():
        return {"medido": False, "motivo": "no se dio --confirmacion o el archivo no existe"}
    c = pd.read_csv(ruta)
    m = c.groupby("config")["tiempo_s"].agg(["mean", "std", "count"])
    actual, optimo = m.loc["actual", "mean"], m.loc["optimo", "mean"]
    return {"medido": True, "archivo": Path(ruta).name,
            "media_actual_s": round(float(actual), 4), "media_optimo_s": round(float(optimo), 4),
            "corridas_por_config": {k: int(v) for k, v in m["count"].items()},
            "mejora_pct": round(100 * (1 - optimo / actual), 1)}


def compatibilidad(raiz):
    """Oro en CSV se escribe y se relee en Parquet sin perder datos."""
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        for t in TABLAS_ORO:
            df = pd.read_csv(raiz / "data" / "oro" / f"{t}.csv")
            ruta = Path(tmp) / f"{t}.parquet"
            df.to_parquet(ruta, index=False)
            try:
                pd.testing.assert_frame_equal(df, pd.read_parquet(ruta), check_dtype=False)
                res[t] = True
            except AssertionError:
                res[t] = False
    return {"csv_lee_el_tablero": (raiz / "data" / "oro" / "ventas_diarias.csv").exists(),
            "parquet_ida_y_vuelta_sin_perdida": res,
            "formatos_demostrados": 1 + int(all(res.values()))}


def tablero(raiz):
    from streamlit.testing.v1 import AppTest

    inicio = time.perf_counter()
    at = AppTest.from_file(str(raiz / "tablero" / "app.py"), default_timeout=120).run()
    return {"excepciones": len(at.exception), "titulos": len(at.title),
            "metricas": [m.label for m in at.metric], "secciones": [s.value for s in at.subheader],
            "avisos": len(at.warning), "mapas_o_graficas_extra": len(at.get("map")),
            "segundos_de_carga": round(time.perf_counter() - inicio, 2)}


def flexibilidad(raiz):
    """Cambiar de tienda sin tocar codigo: variables de entorno TIENDA_LAT / TIENDA_LON."""
    codigo = ("import json; from extractores import config; "
              "print(json.dumps(config.TIENDA_PILOTO))")

    def correr(extra):
        env = {k: v for k, v in os.environ.items() if k not in ("TIENDA_LAT", "TIENDA_LON")}
        env.update(extra)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        out = subprocess.run([sys.executable, "-c", codigo], cwd=raiz, env=env,
                             capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    sin = correr({})
    con = correr({"TIENDA_LAT": "19.2433", "TIENDA_LON": "-103.7250"})  # centro de Colima
    usa_config = "config.TIENDA_PILOTO" in (raiz / "pipeline" / "ejecutar.py").read_text("utf-8")
    return {"sin_variables": sin, "con_variables_de_prueba": con,
            "cambia_sin_editar_codigo": (sin["lat"], sin["lon"]) != (con["lat"], con["lon"]),
            "pipeline_usa_la_configuracion": usa_config}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", default=RAIZ, type=Path)
    ap.add_argument("--confirmacion", type=Path, help="confirmacion.csv del experimento 2^3")
    ap.add_argument("--salida", type=Path)
    args = ap.parse_args()
    raiz = args.raiz.resolve()
    resultado = {
        "medido_en": datetime.now().astimezone().isoformat(timespec="minutes"),
        "entorno": {"sistema": platform.platform(), "python": platform.python_version(),
                    "pandas": pd.__version__},
        "adecuacion_funcional": adecuacion_funcional(raiz),
        "eficiencia_de_desempeno": desempeno(args.confirmacion),
        "compatibilidad": compatibilidad(raiz),
        "capacidad_de_interaccion_tablero": tablero(raiz),
        "flexibilidad": flexibilidad(raiz),
    }
    salida = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(salida + "\n", encoding="utf-8")
    print(salida)


if __name__ == "__main__":
    main()
