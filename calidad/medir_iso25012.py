"""Mediciones ISO/IEC 25012 sobre la capa oro de AbarrotesPOS (solo lectura).

    python calidad/medir_iso25012.py --fecha 2026-11-23 --salida calidad/mediciones/iso25012.json
    python calidad/medir_iso25012.py --comparar RUTA_DE_OTRA_COPIA   # recuperabilidad/portabilidad

No escribe nada en data/. Cada numero de docs/calidad/iso25012.md sale de este script.
Autor: Jose Rey Sanchez Navarro (Calidad, E2), con asistencia de IA (Claude Code).
"""

import argparse
import gzip
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

TABLAS = ["ventas_diarias", "ventas_producto_mes", "fiados_por_cliente"]
LINAJE = ["fuente", "archivo_bronce", "capturado_utc"]
MONEDA = {"ventas_diarias": ["venta", "ganancia", "venta_fiado"],
          "ventas_producto_mes": ["venta", "ganancia"],
          "fiados_por_cliente": ["adeudo_bruto"]}
NOMBRES_SENSIBLES = ["nombre", "telefono", "tel", "correo", "email", "direccion", "domicilio",
                     "rfc", "curp", "celular"]
RE_CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
RE_TELEFONO = re.compile(r"(?<!\d)(?:\d{10}|\d{3}[ -]\d{3}[ -]\d{4}|\d{2}[ -]\d{4}[ -]\d{4})(?!\d)")
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_MES = re.compile(r"^\d{4}-\d{2}$")
RE_FIADO = re.compile(r"^F\d{3}$")


def pct(a, b):
    return round(100 * a / b, 2) if b else None


def leer(oro):
    texto = {t: pd.read_csv(oro / f"{t}.csv", dtype=str, keep_default_na=False) for t in TABLAS}
    num = {t: pd.read_csv(oro / f"{t}.csv") for t in TABLAS}
    return texto, num


def exactitud(raiz, num):
    rep = json.loads((raiz / "calidad" / "reporte-puerta.json").read_text(encoding="utf-8"))
    plata, cuar = rep["ventas_en_plata"], rep["ventas_en_cuarentena"]
    d, p = num["ventas_diarias"], num["ventas_producto_mes"]
    reglas = {
        "venta_negativa": int((d["venta"] < 0).sum() + (p["venta"] < 0).sum()),
        "ganancia_negativa": int((d["ganancia"] < 0).sum() + (p["ganancia"] < 0).sum()),
        "ganancia_mayor_que_venta": int((d["ganancia"] > d["venta"]).sum()
                                        + (p["ganancia"] > p["venta"]).sum()),
        "venta_fiado_mayor_que_venta": int((d["venta_fiado"] > d["venta"]).sum()),
        "piezas_menores_que_tickets": int((d["piezas"] < d["tickets"]).sum()),
        "tickets_no_positivos": int((d["tickets"] <= 0).sum()),
    }
    filas_revisadas = len(d) + len(p)
    return {"ventas_en_plata": plata, "ventas_en_cuarentena": cuar,
            "pct_aceptado_puerta": pct(plata, plata + cuar),
            "reglas_de_negocio_violadas_en_oro": reglas, "filas_oro_revisadas": filas_revisadas,
            "fuente_ventas": rep["fuente_ventas"]}


def completitud(num):
    d = num["ventas_diarias"]
    fechas = pd.to_datetime(d["fecha"])
    rango = pd.date_range(fechas.min(), fechas.max(), freq="D")
    p = num["ventas_producto_mes"]
    combinaciones = p["producto"].nunique() * p["mes"].nunique()
    nulos = {t: {c: int(n) for c, n in df.isna().sum().items() if n and c != "evento"}
             for t, df in num.items()}
    clima = {c: (int(d[c].notna().sum()) if c in d else 0) for c in ("temp_max_c", "lluvia_mm")}
    return {"fecha_min": str(fechas.min().date()), "fecha_max": str(fechas.max().date()),
            "dias_en_rango": len(rango), "dias_con_venta": int(fechas.nunique()),
            "dias_faltantes": int(len(rango.difference(fechas))),
            "fechas_duplicadas": int(fechas.duplicated().sum()),
            "pct_dias_con_venta": pct(fechas.nunique(), len(rango)),
            "columnas_clima_presentes": [c for c in ("temp_max_c", "lluvia_mm") if c in d],
            "dias_con_clima": clima, "pct_dias_con_clima": pct(clima["temp_max_c"], len(rango)),
            "producto_mes_filas": len(p), "producto_mes_combinaciones_posibles": combinaciones,
            "pct_producto_mes": pct(len(p), combinaciones),
            "nulos_fuera_de_evento": nulos}


def consistencia(num):
    d, p, f = num["ventas_diarias"], num["ventas_producto_mes"], num["fiados_por_cliente"]
    pares = {"venta": (d["venta"].sum(), p["venta"].sum()),
             "ganancia": (d["ganancia"].sum(), p["ganancia"].sum()),
             "piezas": (d["piezas"].sum(), p["piezas"].sum()),
             "venta_fiado_vs_adeudo_bruto": (d["venta_fiado"].sum(), f["adeudo_bruto"].sum())}
    return {k: {"tabla_a": round(float(a), 2), "tabla_b": round(float(b), 2),
                "diferencia": round(float(a - b), 6)} for k, (a, b) in pares.items()}


def credibilidad(num):
    total = sum(len(df) for df in num.values())
    conteo = pd.concat([df["fuente"] for df in num.values()]).value_counts()
    return {"filas_oro": total, "por_fuente": {k: int(v) for k, v in conteo.items()},
            "pct_por_fuente": {k: pct(int(v), total) for k, v in conteo.items()}}


def actualidad(num, fecha_eval):
    ultima = pd.to_datetime(num["ventas_diarias"]["fecha"]).max().date()
    cap = max(datetime.fromisoformat(c) for df in num.values() for c in df["capturado_utc"])
    return {"fecha_evaluacion": str(fecha_eval), "ultima_fecha_de_venta": str(ultima),
            "dias_de_atraso": (fecha_eval - ultima).days,
            "ultima_captura_utc": cap.isoformat(),
            "dias_desde_captura": (fecha_eval - cap.date()).days}


def conformidad(oro, texto):
    utf8 = {}
    for t in TABLAS:
        try:
            (oro / f"{t}.csv").read_bytes().decode("utf-8")
            utf8[t] = True
        except UnicodeDecodeError:
            utf8[t] = False
    malas = {"fecha_no_iso8601": int((~texto["ventas_diarias"]["fecha"].str.match(RE_FECHA)).sum()),
             "mes_no_aaaa_mm": int((~texto["ventas_producto_mes"]["mes"].str.match(RE_MES)).sum())}
    tz = 0
    for df in texto.values():
        for c in df["capturado_utc"]:
            try:
                tz += datetime.fromisoformat(c).tzinfo is None
            except ValueError:
                tz += 1
    malas["capturado_utc_sin_zona_o_invalido"] = int(tz)
    no_num = {}
    for t, cols in MONEDA.items():
        for c in cols:
            no_num[f"{t}.{c}"] = int(pd.to_numeric(texto[t][c], errors="coerce").isna().sum())
    return {"utf8_valido": utf8, "valores_no_conformes": malas, "importes_no_numericos": no_num}


def confidencialidad(texto):
    columnas = sorted({c for df in texto.values() for c in df.columns})
    sospechosas = [c for c in columnas if any(s in c.lower() for s in NOMBRES_SENSIBLES)]
    celdas = correos = telefonos = 0
    for df in texto.values():
        for c in df.columns:
            if c in LINAJE:
                continue
            serie = df[c]
            celdas += len(serie)
            correos += int(serie.str.contains(RE_CORREO).sum())
            telefonos += int(serie.str.contains(RE_TELEFONO).sum())
    claves = texto["fiados_por_cliente"]["cliente_fiado"]
    return {"columnas_oro": columnas, "columnas_con_nombre_sensible": sospechosas,
            "celdas_revisadas": celdas, "celdas_con_correo": correos,
            "celdas_con_telefono": telefonos,
            "claves_fiado": int(len(claves)),
            "claves_fiado_anonimas_F000": int(claves.str.match(RE_FIADO).sum())}


def eficiencia(oro, num):
    bytes_oro = sum((oro / f"{t}.csv").stat().st_size for t in TABLAS)
    dias = int(pd.to_datetime(num["ventas_diarias"]["fecha"]).nunique())
    return {"bytes_oro": bytes_oro, "mb_oro": round(bytes_oro / 1_048_576, 3),
            "dias_de_datos": dias, "kb_por_dia": round(bytes_oro / 1024 / dias, 2)}


def precision(texto):
    res = {}
    for t, cols in MONEDA.items():
        for c in cols:
            dec = texto[t][c].str.split(".").str[1].fillna("").str.len()
            res[f"{t}.{c}"] = {"max_decimales": int(dec.max()),
                               "valores_con_mas_de_2_decimales": int((dec > 2).sum()),
                               "valores": int(len(dec))}
    return res


def trazabilidad(raiz, texto):
    total = sum(len(df) for df in texto.values())
    completas = sum(int((df[LINAJE] != "").all(axis=1).sum()) for df in texto.values())
    archivos = sorted({a for df in texto.values() for a in df["archivo_bronce"]})
    verif = {}
    for a in archivos:
        rutas = list((raiz / "data" / "bronce").rglob(a))
        if not rutas:
            verif[a] = {"existe_en_bronce": False}
            continue
        ruta = rutas[0]
        meta_ruta = ruta.parent / f"{a.split('.')[0]}.meta.json"
        meta = json.loads(meta_ruta.read_text(encoding="utf-8"))
        sha = hashlib.sha256(gzip.open(ruta).read()).hexdigest()
        caps = {c for df in texto.values() for c in df.loc[df["archivo_bronce"] == a,
                                                           "capturado_utc"]}
        verif[a] = {"existe_en_bronce": True,
                    "ruta": ruta.relative_to(raiz).as_posix(),
                    "meta_existe": meta_ruta.exists(),
                    "sha256_recalculado_igual_a_meta": sha == meta["sha256"],
                    "sha256_meta": meta["sha256"],
                    "capturado_utc_igual_a_meta": caps == {meta["capturado_utc"]}}
    return {"filas_oro": total, "filas_con_linaje_completo": completas,
            "pct_linaje_completo": pct(completas, total), "archivos_bronce": verif}


def comprensibilidad(oro, texto):
    dic = oro / "DICCIONARIO.md"
    if not dic.exists():
        return {"diccionario_existe": False, "pct_columnas_documentadas": 0.0}
    contenido = dic.read_text(encoding="utf-8")
    documentadas = set(re.findall(r"^\|\s*`([a-z_0-9]+)`\s*\|", contenido, flags=re.M))
    total = faltan = 0
    faltantes = []
    for t, df in texto.items():
        for c in df.columns:
            total += 1
            if c not in documentadas:
                faltan += 1
                faltantes.append(f"{t}.{c}")
    return {"diccionario_existe": True, "columnas_en_oro": total,
            "columnas_documentadas": total - faltan,
            "pct_columnas_documentadas": pct(total - faltan, total), "faltantes": faltantes}


def comparar(oro, otra):
    res = {}
    for t in TABLAS:
        a, b = oro / f"{t}.csv", Path(otra) / "data" / "oro" / f"{t}.csv"
        if not b.exists():
            res[t] = {"existe_en_otra": False}
            continue
        da, db = pd.read_csv(a), pd.read_csv(b)
        iguales_bytes = a.read_bytes() == b.read_bytes()
        try:
            pd.testing.assert_frame_equal(da, db, check_exact=False, rtol=0, atol=1e-6)
            iguales_valor = True
        except AssertionError:
            iguales_valor = False
        ta = pd.read_csv(a, dtype=str, keep_default_na=False)
        tb = pd.read_csv(b, dtype=str, keep_default_na=False)
        celdas_distintas = int((ta != tb).to_numpy().sum()) if ta.shape == tb.shape else None
        res[t] = {"filas": [len(da), len(db)], "bytes_identicos": iguales_bytes,
                  "valores_iguales_tolerancia_1e-6": iguales_valor,
                  "celdas_con_texto_distinto": celdas_distintas}
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", default=Path(__file__).resolve().parents[1], type=Path)
    ap.add_argument("--fecha", default=str(date.today()), help="fecha de evaluacion AAAA-MM-DD")
    ap.add_argument("--salida", type=Path, help="archivo JSON donde guardar el resultado")
    ap.add_argument("--comparar", type=Path, help="raiz de otra copia para comparar su oro")
    args = ap.parse_args()
    raiz = args.raiz.resolve()
    oro = raiz / "data" / "oro"
    texto, num = leer(oro)
    resultado = {
        "raiz_medida": raiz.name, "fecha_evaluacion": args.fecha,
        "pandas": pd.__version__,
        "exactitud": exactitud(raiz, num),
        "completitud": completitud(num),
        "consistencia": consistencia(num),
        "credibilidad": credibilidad(num),
        "actualidad": actualidad(num, date.fromisoformat(args.fecha)),
        "conformidad": conformidad(oro, texto),
        "confidencialidad": confidencialidad(texto),
        "eficiencia": eficiencia(oro, num),
        "precision": precision(texto),
        "trazabilidad": trazabilidad(raiz, texto),
        "comprensibilidad": comprensibilidad(oro, texto),
    }
    if args.comparar:
        resultado["comparacion_con_otra_copia"] = comparar(oro, args.comparar.resolve())
    salida = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(salida + "\n", encoding="utf-8")
    print(salida)


if __name__ == "__main__":
    main()
