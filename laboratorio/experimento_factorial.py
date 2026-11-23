"""Experimento factorial E2 (ruta ingenieria) sobre el propio pipeline de AbarrotesPOS.

Pregunta: ¿que configuracion procesa mas rapido las ventas de la tienda?
Tarea medida: leer el archivo de tickets, calcular venta y ganancia por producto y dia,
y escribir el resultado. Se corre en local; no toca ningun sitio ajeno.

Factores del 2^3 (nivel -1 / +1):
  A procesos : 1 proceso  / 4 procesos
  B tipos    : texto      / categorico (category)
  C formato  : CSV        / Parquet
Factor extra para el 2^4 y el 2^(4-1):
  D compresion: sin compresion / con compresion (gzip en CSV, snappy en Parquet)
Respuestas: tiempo_s (principal) y tamano_mb.
Bloque: la maquina donde se corre (variable MAQUINA o el nombre del equipo).

Uso:
  python -m laboratorio.experimento_factorial correr --replicas 3
  python -m laboratorio.experimento_factorial dos-factores --replicas 3
  python -m laboratorio.experimento_factorial matrices
  python -m laboratorio.experimento_factorial analizar
  python -m laboratorio.experimento_factorial confirmar --corridas 5
"""

import argparse
import itertools
import os
import platform
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import ventas_demo

RES = Path(__file__).resolve().parent / "resultados"
NIVELES = {
    "A": {-1: 1, 1: 4},
    "B": {-1: "texto", 1: "categorico"},
    "C": {-1: "csv", 1: "parquet"},
    "D": {-1: "sin", 1: "con"},
}
SEMILLA = 2026


def datos_base(filas=None):
    df = ventas_demo.generar(desde="2025-01-01", hasta="2026-10-31")
    if filas:
        df = df.sample(n=min(filas, len(df)), random_state=SEMILLA)
    return df


def _agregar(trozo):
    t = trozo.assign(importe=trozo["piezas"] * trozo["precio_unitario"],
                     ganancia=trozo["piezas"] * (trozo["precio_unitario"]
                                                 - trozo["costo_unitario"]))
    return t.groupby(["fecha", "producto"], observed=True)[["piezas", "importe", "ganancia"]].sum()


def _escribir(df, ruta, formato, compresion):
    if formato == "csv":
        df.to_csv(ruta, index=False, compression="gzip" if compresion == "con" else None)
    else:
        df.to_parquet(ruta, index=False, compression="snappy" if compresion == "con" else None)


def _leer(ruta, formato, tipos):
    cat = ["producto", "categoria", "forma_pago", "evento", "fuente"]
    if formato == "csv":
        # Se lee como texto y se convierte despues: con dtype="category" directo, pandas arma
        # categorias por pedazos y truena cuando "evento" viene vacio en un pedazo (defecto 1).
        df = pd.read_csv(ruta, dtype={c: str for c in cat}, keep_default_na=False)
        if tipos == "categorico":
            df[cat] = df[cat].astype("category")
        return df
    df = pd.read_parquet(ruta)
    if tipos == "categorico":
        df[cat] = df[cat].astype("category")
    return df


def corrida(df, procesos, tipos, formato, compresion, carpeta):
    """Mide una corrida completa. El archivo de entrada se prepara fuera del cronometro."""
    ext = "csv" if formato == "csv" else "parquet"
    entrada = carpeta / f"entrada.{ext}"
    _escribir(df, entrada, formato, compresion)
    salida = carpeta / f"salida.{ext}"
    t0 = time.perf_counter()
    datos = _leer(entrada, formato, tipos)
    if procesos == 1:
        res = _agregar(datos)
    else:
        cortes = np.linspace(0, len(datos), procesos + 1).astype(int)
        trozos = [datos.iloc[a:b] for a, b in zip(cortes[:-1], cortes[1:], strict=True)]
        with ProcessPoolExecutor(max_workers=procesos) as ex:
            res = pd.concat(ex.map(_agregar, trozos)).groupby(level=[0, 1]).sum()
    _escribir(res.reset_index(), salida, formato, compresion)
    tiempo = time.perf_counter() - t0
    return tiempo, entrada.stat().st_size / 1e6


def plan_2k(factores, replicas, semilla=SEMILLA, generador=None):
    """Matriz codificada, replicada y en orden aleatorio. generador: ('D', 'ABC') para 2^(4-1)."""
    base = [f for f in factores if not generador or f != generador[0]]
    filas = [dict(zip(base, c, strict=True)) for c in itertools.product([-1, 1], repeat=len(base))]
    if generador:
        nuevo, palabra = generador
        for f in filas:
            f[nuevo] = int(np.prod([f[x] for x in palabra]))
    plan = pd.DataFrame([{**f, "tratamiento": i + 1, "replica": r + 1}
                         for r in range(replicas) for i, f in enumerate(filas)])
    plan = plan.sample(frac=1, random_state=semilla).reset_index(drop=True)
    plan.insert(0, "orden", range(1, len(plan) + 1))
    return plan


def _maquina():
    return os.environ.get("MAQUINA", platform.node() or "desconocida")


def correr(replicas, filas, con_d=False, archivo="corridas_2k3.csv"):
    factores = ["A", "B", "C", "D"] if con_d else ["A", "B", "C"]
    plan = plan_2k(factores, replicas)
    df = datos_base(filas)
    tmp = Path(tempfile.mkdtemp(prefix="exp_"))
    salida = []
    try:
        for _, f in plan.iterrows():
            niveles = {k: NIVELES[k][f[k]] for k in factores}
            t, mb = corrida(df, niveles["A"], niveles["B"], niveles["C"],
                            niveles.get("D", "sin"), tmp)
            salida.append({**f.to_dict(), **{f"{k}_nivel": v for k, v in niveles.items()},
                           "tiempo_s": round(t, 4), "tamano_mb": round(mb, 3),
                           "bloque": _maquina(), "filas": len(df)})
            print(f"corrida {int(f['orden'])}/{len(plan)}: {niveles} -> {t:.3f} s")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    RES.mkdir(parents=True, exist_ok=True)
    out = RES / archivo
    nuevo = pd.DataFrame(salida)
    if out.exists():  # otra maquina = otro bloque; se acumulan
        nuevo = pd.concat([pd.read_csv(out), nuevo], ignore_index=True)
    nuevo.to_csv(out, index=False)
    print(f"guardado {out} ({len(nuevo)} corridas)")


def dos_factores(replicas):
    """Dos factores, uno con 3 niveles: tamano (3 niveles) x formato (2). ANOVA de dos vias."""
    df_total = datos_base()
    tamanos = {"chico": len(df_total) // 4, "mediano": len(df_total) // 2, "grande": len(df_total)}
    plan = [(t, fmt, r) for r in range(replicas) for t in tamanos for fmt in ("csv", "parquet")]
    rng = np.random.default_rng(SEMILLA)
    rng.shuffle(plan)
    tmp = Path(tempfile.mkdtemp(prefix="exp2_"))
    filas = []
    try:
        for i, (t, fmt, r) in enumerate(plan, 1):
            df = df_total.sample(n=tamanos[t], random_state=SEMILLA)
            seg, _ = corrida(df, 1, "texto", fmt, "sin", tmp)
            filas.append({"orden": i, "tamano": t, "formato": fmt, "replica": r + 1,
                          "tiempo_s": round(seg, 4), "bloque": _maquina()})
            print(f"{i}/{len(plan)} {t} {fmt}: {seg:.3f} s")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    RES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas).to_csv(RES / "corridas_dos_factores.csv", index=False)


def matrices():
    """Matriz 2^4 completa y 2^(4-1) con D = ABC (I = ABCD, resolucion IV) y sus alias."""
    completo = plan_2k(list("ABCD"), 1).sort_values("tratamiento").drop(columns="orden")
    fracc = plan_2k(list("ABCD"), 1, generador=("D", "ABC")).sort_values("tratamiento")
    alias = pd.DataFrame([
        ("A", "BCD"), ("B", "ACD"), ("C", "ABD"), ("D", "ABC"),
        ("AB", "CD"), ("AC", "BD"), ("AD", "BC"), ("I", "ABCD"),
    ], columns=["efecto", "confundido_con"])
    RES.mkdir(parents=True, exist_ok=True)
    completo.to_csv(RES / "matriz_2k4_completa.csv", index=False)
    fracc.drop(columns="orden").to_csv(RES / "matriz_2k4-1_fraccionada.csv", index=False)
    alias.to_csv(RES / "alias_2k4-1.csv", index=False)
    print(f"2^4 completo: {len(completo)} corridas por replica; 2^(4-1): {len(fracc)} "
          f"(ahorro {1 - len(fracc) / len(completo):.0%}). Resolucion IV: efectos principales "
          "solo confundidos con interacciones triples; las dobles entre si.")


def analizar(archivo="corridas_2k3.csv"):
    import statsmodels.formula.api as smf
    from scipy import stats
    from statsmodels.stats.anova import anova_lm

    d = pd.read_csv(RES / archivo)
    bloque = " + C(bloque)" if d["bloque"].nunique() > 1 else ""
    modelo = smf.ols(f"tiempo_s ~ A * B * C{bloque}", data=d).fit()
    tabla = anova_lm(modelo, typ=2)
    efectos = (2 * modelo.params.drop("Intercept")).rename("efecto_s")  # efecto = 2 * coef
    res = modelo.resid
    supuestos = {
        "shapiro_p": stats.shapiro(res).pvalue,
        "levene_p": stats.levene(*[g["tiempo_s"] for _, g in d.groupby(["A", "B", "C"])]).pvalue,
    }
    medias = d.groupby(["A_nivel", "B_nivel", "C_nivel"])["tiempo_s"].agg(["mean", "std", "count"])
    optimo = medias["mean"].idxmin()
    tabla.to_csv(RES / "anova_2k3.csv")
    efectos.to_csv(RES / "efectos_2k3.csv")
    medias.to_csv(RES / "medias_tratamiento.csv")
    print(tabla.round(4), "\n\nEfectos (s):\n", efectos.round(4), "\n\nSupuestos:", supuestos)
    print("\nCombinacion mas rapida (procesos, tipos, formato):", optimo,
          f"-> {medias.loc[optimo, 'mean']:.3f} s")
    _graficas(d, res, modelo)
    if (RES / "corridas_dos_factores.csv").exists():
        d2 = pd.read_csv(RES / "corridas_dos_factores.csv")
        m2 = smf.ols("tiempo_s ~ C(tamano) * C(formato)", data=d2).fit()
        t2 = anova_lm(m2, typ=2)
        t2.to_csv(RES / "anova_dos_factores.csv")
        print("\nANOVA dos vias (tamano x formato):\n", t2.round(4))


def _graficas(d, res, modelo):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from statsmodels.graphics.factorplots import interaction_plot

    fig, ejes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, (x, traza) in zip(ejes, [("A_nivel", "C_nivel"), ("B_nivel", "C_nivel"),
                                     ("A_nivel", "B_nivel")], strict=True):
        interaction_plot(d[x].astype(str), d[traza].astype(str), d["tiempo_s"], ax=ax)
        ax.set_title(f"Interaccion {x[0]} x {traza[0]}")
    fig.tight_layout()
    fig.savefig(RES / "interacciones.png", dpi=110)
    fig, ejes = plt.subplots(1, 2, figsize=(10, 4))
    ejes[0].scatter(modelo.fittedvalues, res)
    ejes[0].axhline(0, color="gray")
    ejes[0].set_title("Residuos vs ajustados")
    from scipy import stats

    stats.probplot(res, plot=ejes[1])
    fig.tight_layout()
    fig.savefig(RES / "residuos.png", dpi=110)


def confirmar(corridas, filas):
    """Corrida de confirmacion: el optimo del ANOVA contra la configuracion actual (-1,-1,-1)."""
    medias = pd.read_csv(RES / "medias_tratamiento.csv")
    mejor = medias.loc[medias["mean"].idxmin()]
    df = datos_base(filas)
    tmp = Path(tempfile.mkdtemp(prefix="conf_"))
    filas_out = []
    try:
        for i in range(corridas):
            for etiqueta, cfg in [("actual", (1, "texto", "csv")),
                                  ("optimo", (int(mejor["A_nivel"]), mejor["B_nivel"],
                                              mejor["C_nivel"]))]:
                t, _ = corrida(df, *cfg, "sin", tmp)
                filas_out.append({"corrida": i + 1, "config": etiqueta, "tiempo_s": round(t, 4)})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    c = pd.DataFrame(filas_out)
    c.to_csv(RES / "confirmacion.csv", index=False)
    m = c.groupby("config")["tiempo_s"].mean()
    print(m, f"\nMejora: {1 - m['optimo'] / m['actual']:.1%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["correr", "correr-2k4", "dos-factores", "matrices",
                                       "analizar", "confirmar"])
    ap.add_argument("--replicas", type=int, default=3)
    ap.add_argument("--filas", type=int, default=None, help="muestra de tickets (prueba rapida)")
    ap.add_argument("--corridas", type=int, default=5)
    a = ap.parse_args()
    if a.accion == "correr":
        correr(a.replicas, a.filas)
    elif a.accion == "correr-2k4":
        correr(a.replicas, a.filas, con_d=True, archivo="corridas_2k4.csv")
    elif a.accion == "dos-factores":
        dos_factores(a.replicas)
    elif a.accion == "matrices":
        matrices()
    elif a.accion == "analizar":
        analizar()
    else:
        confirmar(a.corridas, a.filas)


if __name__ == "__main__":
    main()
