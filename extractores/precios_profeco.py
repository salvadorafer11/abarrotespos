"""Precios de mercado (J6): PROFECO "Quién es Quién en los Precios" (QQP), datos abiertos.

Web scraping del portal de datos abiertos de PROFECO:
1. Se lee la página del portal (HTML) y se toma el enlace al archivo del año más reciente
   (docs/qqp/<año>.rar). El portal no tiene robots.txt (responde 404): se permite, igual que
   la regla de la biblioteca estándar (ver extractores/base.py).
2. Se descarga el .rar (~75 MB) con el ExtractorEtico (User-Agent honesto y pausa).
3. Del mes más reciente se guardan en bronce solo las filas de la zona: Colima si PROFECO la
   registra; si no, la zona metropolitana de Guadalajara (config.QQP_ZONAS). El .meta.json
   guarda el SHA-256 del .rar completo, para rastrear cada precio hasta el archivo oficial.

Por qué no el sitio de una cadena: Soriana prohíbe en sus términos de uso "la utilización de
tecnología para realizar la extracción [...] de cualquier información incluida en el SITIO";
La Comer, Chedraui y Walmart bloquean la búsqueda o el catálogo en su robots.txt. La API de
qqp.profeco.gob.mx pide usuario y contraseña, así que tampoco se usa.

Uso:  python -m extractores.precios_profeco
"""

import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urljoin

from extractores import bronce, config
from extractores.base import ExtractorEtico

COLUMNAS = ["producto", "presentacion", "marca", "categoria", "catalogo", "precio",
            "fecha_registro", "cadena_comercial", "giro", "nombre_comercial", "direccion",
            "estado", "municipio", "latitud", "longitud"]


def enlace_mas_reciente(pagina, base=config.QQP_PORTAL):
    """URL del .rar del año más reciente que aparece en la página del portal."""
    anios = {int(a): urljoin(base, ruta)
             for ruta, a in re.findall(r'href="([^"]*qqp/(\d{4})\.rar)"', pagina)}
    if not anios:
        raise RuntimeError("La página de PROFECO ya no enlaza archivos qqp/<año>.rar")
    return anios[max(anios)]


def mes_mas_reciente(miembros):
    """CSV del mes más reciente (sus dos quincenas, si ya están): '2026/10-2026_Q1.csv'..."""
    fechas = {}
    for m in miembros:
        r = re.search(r"(\d{2})-(\d{4})_Q\d\.csv$", m)
        if r:
            fechas.setdefault((int(r.group(2)), int(r.group(1))), []).append(m)
    if not fechas:
        raise RuntimeError("El .rar de PROFECO no trae archivos MM-AAAA_Qn.csv")
    clave = max(fechas)
    return f"{clave[0]}-{clave[1]:02d}", sorted(fechas[clave])


def herramienta():
    """Programa para abrir el .rar (RAR5): bsdtar (libarchive), unrar o 7-Zip. En Windows,
    el tar.exe del sistema es bsdtar."""
    for nombre, tipo in (("bsdtar", "bsdtar"), ("unrar", "unrar"), ("7zz", "7z"), ("7z", "7z")):
        ruta = shutil.which(nombre)
        if ruta:
            return tipo, ruta
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "tar.exe"
    if windows.exists():
        return "bsdtar", str(windows)
    raise RuntimeError("Para abrir el .rar hace falta bsdtar (libarchive-tools), unrar o 7z")


def _comando(tipo, exe, rar, miembro=None):
    if miembro is None:  # listar
        return {"bsdtar": [exe, "-tf", rar], "unrar": [exe, "lb", rar],
                "7z": [exe, "l", "-ba", "-slt", rar]}[tipo]
    return {"bsdtar": [exe, "-xOf", rar, miembro], "unrar": [exe, "p", "-inul", rar, miembro],
            "7z": [exe, "x", "-so", rar, miembro]}[tipo]


def listar(rar, tipo, exe):
    salida = subprocess.run(_comando(tipo, exe, rar), capture_output=True, text=True,
                            check=True).stdout
    if tipo == "7z":
        return [ln[7:] for ln in salida.splitlines() if ln.startswith("Path = ")]
    return [ln.strip() for ln in salida.splitlines() if ln.strip()]


def filas_de_zona(lineas, zonas=config.QQP_ZONAS):
    """Reparte las filas del CSV por zona (estado + municipio). Devuelve {zona: [filas]}."""
    claves = {(estado, municipio): nombre for nombre, estado, municipios in zonas
              for municipio in municipios}
    por_zona = {nombre: [] for nombre, _, _ in zonas}
    for fila in csv.DictReader(lineas):
        zona = claves.get((fila.get("estado"), fila.get("municipio")))
        if zona:
            por_zona[zona].append(fila)
    return por_zona


def elegir_zona(por_zona, zonas=config.QQP_ZONAS):
    """La primera zona de la lista que sí tiene precios."""
    for nombre, estado, municipios in zonas:
        if por_zona.get(nombre):
            return nombre, estado, municipios
    raise RuntimeError("PROFECO no trae precios de ninguna zona de config.QQP_ZONAS")


def capturar(extractor=None):
    ex = extractor or ExtractorEtico(pausa=2.0, timeout=120)
    pagina = ex.get(config.QQP_PORTAL).text
    url = enlace_mas_reciente(pagina)
    r = ex.get(url)
    tipo, exe = herramienta()
    with tempfile.TemporaryDirectory() as tmp:
        rar = str(Path(tmp) / Path(url).name)
        Path(rar).write_bytes(r.content)
        mes, miembros = mes_mas_reciente(listar(rar, tipo, exe))
        por_zona = {}
        for miembro in miembros:
            # El CSV se lee como flujo (cada quincena pesa ~200 MB sin comprimir).
            proc = subprocess.Popen(_comando(tipo, exe, rar, miembro), stdout=subprocess.PIPE)
            for zona, filas in filas_de_zona(io.TextIOWrapper(proc.stdout,
                                                              encoding="utf-8-sig")).items():
                por_zona.setdefault(zona, []).extend(filas)
            if proc.wait() != 0:
                raise RuntimeError(f"No se pudo leer {miembro} del .rar ({tipo})")
    zona, estado, municipios = elegir_zona(por_zona)
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=COLUMNAS, extrasaction="ignore",
                              lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(por_zona[zona])
    huella = hashlib.sha256(r.content).hexdigest()
    clave = re.sub(r"[^a-z]+", "_", zona.lower().encode("ascii", "ignore").decode()).strip("_")
    ruta = bronce.guardar(
        "profeco_qqp",
        salida.getvalue().encode("utf-8"),
        {"url": url, "portal": config.QQP_PORTAL, "catalogo": config.QQP_CATALOGO,
         "licencia": config.QQP_LICENCIA, "archivo_origen": Path(url).name,
         "archivo_origen_sha256": huella, "archivo_origen_bytes": len(r.content),
         "archivo_origen_modificado": r.headers.get("Last-Modified", ""),
         "miembros": miembros, "mes": mes, "zona": zona, "estado": estado,
         "municipios": municipios,
         "zonas_sin_datos": [n for n, _, _ in config.QQP_ZONAS if not por_zona.get(n)],
         "nota": "solo las filas de la zona; el .rar completo se identifica por su SHA-256"},
        subruta=mes,
        nombre=f"qqp_{clave}_{mes}",
        ext="csv",
    )
    return ruta, len(por_zona[zona])


def main():
    inicio = bronce.ahora_utc()
    fila = {"ejecucion_id": bronce.id_ejecucion(), "disparador": bronce.disparador(),
            "fuente": "profeco_qqp", "inicio_utc": inicio.isoformat()}
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
