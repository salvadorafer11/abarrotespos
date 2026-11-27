"""Precios de mercado (J6): compara los precios de la tienda con los de PROFECO QQP.

Cada producto del catálogo de la tienda se empareja con sus equivalentes en PROFECO (mismo
producto, varias marcas y tamaños parecidos). Los precios se llevan a la misma cantidad que
vende la tienda (p. ej. un "Caja 946 Ml." se lleva a 1 L) y en cada tienda de PROFECO se toma
la opción más barata. Con eso sale, por producto:
  - la mediana del mercado (contra ella se compara el precio de la tienda) y
  - la mejor alternativa: la tienda y la marca más baratas (contra ella se compara el costo:
    si es menor, conviene surtir ahí).

    python -m pipeline.ejecutar   # escribe data/plata/precios_mercado.csv y dos tablas de oro
"""

import gzip
import io
import json
import re

import pandas as pd

from extractores import config

# producto de la tienda -> (producto PROFECO, presentación, excluir, unidad, cantidad, qué es)
# Las expresiones son regulares y sin distinguir mayúsculas; "presentación" y "excluir" se
# buscan en el texto "<presentación> | <marca>". La unidad es "ml", "g" o "pieza"; la cantidad
# es lo que trae el producto de la tienda en esa unidad.
COLAS = r"\| (?:Coca Cola|Pepsi|Big Cola)\b"
EQUIVALENCIAS = {
    "Refresco cola 600 ml": (r"^Refresco$", r"600 Ml.*" + COLAS, r"light|zero|sin az", "ml",
                             600, "Refresco de cola 600 ml (Coca Cola, Pepsi)"),
    "Refresco cola 2.5 L": (r"^Refresco$", r"\b(?:2|2\.5|3) Lt.*" + COLAS,
                            r"(?<!no )retornable|light|zero|sin az", "ml", 2500,
                            "Refresco de cola de 2 a 3 L, llevado a 2.5 L"),
    "Agua natural 1 L": (r"^Agua Sin Gas$", r"Botella 1 Lt", r"sabor|lim[oó]n|jamaica", "ml",
                         1000, "Agua natural de 1 L"),
    "Cerveza lata 355 ml": (r"^Cerveza$", r"Latas? de 355", None, "ml", 355,
                            "Cerveza en lata de 355 ml (precio por lata de los paquetes)"),
    "Jugo 1 L": (r"^Jugo de Fruta$", r"1 Lt|9[46]\d Ml", None, "ml", 1000,
                 "Jugo en caja de 946 ml a 1 L"),
    "Leche entera 1 L": (r"^Leche (?:Ultra)?pasteurizada$", r"1 Lt\. Entera", None, "ml", 1000,
                         "Leche entera de 1 L"),
    "Yogur bebible 250 g": (r"^Yoghurt$", r"Bebible", None, "g", 250,
                            "Yogur bebible, llevado a 250 g"),
    "Queso fresco 250 g": (r"^Queso (?:Panela|Fresco)$", r"Gr", None, "g", 250,
                           "Queso panela o fresco, llevado a 250 g"),
    "Huevo blanco 1 kg": (r"^Huevo$", r"Granel\. Blanco", None, "g", 1000,
                          "Huevo blanco a granel, 1 kg"),
    "Tortilla de maiz 1 kg": (r"^Tortilla de Ma[ií]z$", r"^1 Kg\. Granel \|", None, "g", 1000,
                              "Tortilla de maíz a granel, 1 kg"),
    "Frijol bayo 1 kg": (r"^Frijol$", r"Bayo|Pinto", None, "g", 1000,
                         "Frijol bayo o pinto, llevado a 1 kg"),
    "Arroz 1 kg": (r"^Arroz$", r"Super Extra|Granel", r"integral|quebrado", "g", 1000,
                   "Arroz súper extra, llevado a 1 kg"),
    "Aceite vegetal 1 L": (r"^Aceite$", r"Vegetal|Canola|Soya|Ma[ií]z", None, "ml", 1000,
                           "Aceite vegetal, canola o soya, llevado a 1 L"),
    "Azucar estandar 1 kg": (r"^Az[uú]car$", r"Est[aá]ndar", None, "g", 1000,
                             "Azúcar estándar, llevada a 1 kg"),
    "Sopa de pasta 200 g": (r"^Pasta para Sopa$", r"200 Gr", None, "g", 200,
                            "Pasta para sopa de 200 g"),
    "Atun en lata 140 g": (r"^At[uú]n$", r"^Lata 1[2-4]\d Gr", None, "g", 140,
                           "Atún en lata de 120 a 140 g, llevado a 140 g"),
    "Pan de caja grande": (r"^Pan de Caja$", r"Grande .*Blanco", None, "g", 620,
                           "Pan de caja blanco grande, llevado a 620 g"),
    "Pan dulce pieza": (r"^Pan Dulce$", r"Pieza", None, "pieza", 1, "Pan dulce, una pieza"),
    "Jabon de lavanderia 1 kg": (r"^Detergente P/ropa", r"1 Kg\. Polvo", None, "g", 1000,
                                 "Detergente en polvo para ropa, 1 kg"),
    "Papel higienico 4 rollos": (r"^Papel Higi[eé]nico$", r"\b4 Rollos", None, "pieza", 1,
                                 "Papel higiénico, paquete de 4 rollos"),
    "Cloro 1 L": (r"^Blanqueador$", r"9\d0 Ml|1 Lt", None, "ml", 1000,
                  "Blanqueador (cloro) de 930 ml a 1 L, llevado a 1 L"),
}
# Solo se aceptan presentaciones de tamaño parecido (por pieza): un garrafón o un paquete de
# 24 rollos saldrían más baratos por unidad y la comparación no sería justa.
RANGO_TAMANO = (0.4, 2.6)
# Precios fuera de este rango contra la mediana del producto se toman como error de captura.
RANGO_ATIPICO = (0.35, 3.0)
# Marcas propias de las cadenas: son alternativas válidas (y suelen ser las más baratas), pero
# se señalan para que el dueño sepa que no es la misma marca que vende él.
MARCAS_PROPIAS = (r"^(?:Aurrera|Great Value|Chedraui|Selecto Brand|Fresh Label|Prec[ií]ssimo"
                  r"|Valley Foods|Member'?s Mark|Sabemas|Soriana)\b")
COLUMNAS_PLATA = ["producto_tienda", "producto", "presentacion", "marca", "marca_propia",
                  "precio", "cantidad", "precio_equivalente", "fecha_registro",
                  "cadena_comercial", "giro", "nombre_comercial", "municipio", "latitud",
                  "longitud", "zona", "fuente", "archivo_bronce", "capturado_utc"]
LINAJE = ["fuente", "archivo_bronce", "capturado_utc"]
COLUMNAS_CADENA = ["cadena_comercial", "productos", "indice", "mas_barata_en", "tiendas",
                   *LINAJE]


def cantidad(presentacion, unidad, por_pieza=False):
    """Cantidad de la presentación en ml, g o piezas (None si no se puede leer).
    'Paquete con 12 Latas de 355 Ml.' -> 4260 ml (355 con por_pieza=True);
    'Bolsa Plástico 2 Kg.' -> 2000 g."""
    if unidad == "pieza":
        return 1.0
    texto = presentacion.lower()
    tam = re.search(r"(\d+(?:\.\d+)?)\s*(ml|lt|l|gr|g|kg)\b", texto)
    if not tam:
        return None
    valor, medida = float(tam.group(1)), tam.group(2)
    valor *= {"ml": 1, "lt": 1000, "l": 1000, "gr": 1, "g": 1, "kg": 1000}[medida]
    if (medida in ("ml", "lt", "l")) != (unidad == "ml"):
        return None  # gramos donde se esperaban mililitros, o al revés
    piezas = re.search(r"con\s+(\d+)\s+(?:latas|botellas|piezas)", texto)
    return valor if por_pieza or not piezas else valor * int(piezas.group(1))


def leer_bronce(ruta):
    """Filas de bronce + linaje (y la zona, que viene en el .meta.json)."""
    with gzip.open(ruta, "rb") as f:
        df = pd.read_csv(io.BytesIO(f.read()))
    meta = json.loads((ruta.parent / f"{ruta.name.split('.')[0]}.meta.json")
                      .read_text(encoding="utf-8"))
    return df.assign(zona=meta.get("zona", ""), fuente="profeco_qqp", archivo_bronce=ruta.name,
                     capturado_utc=meta["capturado_utc"])


def plata(crudo):
    """Precios de PROFECO que equivalen a un producto de la tienda, ya llevados a la misma
    cantidad. Si una tienda registró el mismo artículo dos veces, queda el más reciente."""
    if crudo.empty:
        return pd.DataFrame(columns=COLUMNAS_PLATA)
    df = crudo[crudo["giro"].isin(config.QQP_GIROS)].copy()
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
    df["marca"] = df["marca"].fillna("S/M")
    df = df[df["precio"] > 0]
    df = (df.sort_values("fecha_registro")
          .drop_duplicates(["nombre_comercial", "producto", "presentacion", "marca"], keep="last"))
    texto = df["presentacion"] + " | " + df["marca"]
    partes = []
    for propio, (prod, pres, excluir, unidad, cant, _) in EQUIVALENCIAS.items():
        elegido = (df["producto"].str.contains(prod, case=False, regex=True)
                   & texto.str.contains(pres, case=False, regex=True))
        if excluir:
            elegido &= ~texto.str.contains(excluir, case=False, regex=True)
        m = df[elegido]
        # pd.to_numeric: con pandas 3, un map sobre una serie vacía de texto sigue siendo texto.
        pieza = pd.to_numeric(m["presentacion"].map(
            lambda p, u=unidad: cantidad(p, u, por_pieza=True)), errors="coerce")
        m = m[pieza.between(cant * RANGO_TAMANO[0], cant * RANGO_TAMANO[1])]
        m = m.assign(cantidad=pd.to_numeric(m["presentacion"].map(
            lambda p, u=unidad: cantidad(p, u)), errors="coerce"))
        m = m.assign(producto_tienda=propio,
                     precio_equivalente=(m["precio"] / m["cantidad"] * cant).round(2))
        relativo = m["precio_equivalente"] / m["precio_equivalente"].median()
        partes.append(m[relativo.between(*RANGO_ATIPICO)])
    salida = pd.concat(partes, ignore_index=True)
    salida["marca_propia"] = salida["marca"].str.contains(MARCAS_PROPIAS, case=False, regex=True)
    return salida[COLUMNAS_PLATA]


def oro(precios, ventas):
    """(comparativo por producto, índice de precios por cadena).

    - Mediana del mercado: de todas las ofertas del producto (todas las marcas y tiendas);
      es el precio típico y contra ella se compara el precio de la tienda.
    - Mejor alternativa: la oferta más barata (puede ser marca propia de la cadena); contra
      ella se compara el costo: si es menor, conviene surtir ahí.
    - Índice por cadena: 100 = mediana del mercado; 90 = 10 % más barata en promedio."""
    ultimo = ventas.sort_values("fecha").groupby("producto").last()
    desde = ventas["fecha"].max() - pd.Timedelta(days=30)
    piezas_mes = ventas[ventas["fecha"] > desde].groupby("producto")["piezas"].sum()
    filas = []
    for propio in ultimo.index:
        tienda = ultimo.loc[propio]
        fila = {"producto": propio, "categoria": tienda["categoria"],
                "tu_precio": tienda["precio_unitario"], "tu_costo": tienda["costo_unitario"],
                "piezas_mes": int(piezas_mes.get(propio, 0)),
                "equivalente": EQUIVALENCIAS[propio][5] if propio in EQUIVALENCIAS else ""}
        p = precios[precios["producto_tienda"] == propio].sort_values("precio_equivalente")
        if len(p):
            mejor = p.iloc[0]
            # El ahorro al surtir se mide con la marca comercial más barata (lo que vende la
            # tienda); la marca propia queda como dato aparte porque es otro producto.
            comercial = p[~p["marca_propia"].astype(bool)]
            mc = comercial.iloc[0] if len(comercial) else mejor
            mediana = p["precio_equivalente"].median()
            fila.update(
                ofertas=len(p), tiendas=p["nombre_comercial"].nunique(),
                mercado_mediana=round(mediana, 2), mercado_min=mejor["precio_equivalente"],
                mercado_max=p["precio_equivalente"].max(),
                mejor_tienda=mejor["nombre_comercial"], mejor_cadena=mejor["cadena_comercial"],
                mejor_marca=mejor["marca"], mejor_marca_propia=bool(mejor["marca_propia"]),
                mejor_presentacion=mejor["presentacion"], mejor_precio_real=mejor["precio"],
                comercial_tienda=mc["nombre_comercial"], comercial_cadena=mc["cadena_comercial"],
                comercial_marca=mc["marca"], comercial_presentacion=mc["presentacion"],
                comercial_precio=mc["precio_equivalente"],
                diferencia_pct=round((tienda["precio_unitario"] / mediana - 1) * 100, 1),
                ahorro_por_pieza=round(tienda["costo_unitario"] - mc["precio_equivalente"], 2),
                fecha_precios=p["fecha_registro"].max(), zona=mejor["zona"],
                **{c: mejor[c] for c in LINAJE})
        filas.append(fila)
    comparativo = pd.DataFrame(filas)
    if "ofertas" not in comparativo:
        return comparativo, pd.DataFrame(columns=COLUMNAS_CADENA)
    comparativo["ahorro_mes"] = (comparativo["ahorro_por_pieza"].clip(lower=0)
                                 * comparativo["piezas_mes"]).round(2)
    mediana = precios.groupby("producto_tienda")["precio_equivalente"].transform("median")
    rel = (precios.assign(relativo=precios["precio_equivalente"] / mediana * 100)
           .groupby(["cadena_comercial", "producto_tienda"], as_index=False)
           .agg(relativo=("relativo", "median"), tiendas=("nombre_comercial", "nunique"),
                **{c: (c, "first") for c in LINAJE}))
    mas_barata = (precios.sort_values("precio_equivalente").drop_duplicates("producto_tienda")
                  ["cadena_comercial"].value_counts())
    cadenas = (rel.groupby("cadena_comercial")
               .agg(productos=("producto_tienda", "nunique"), indice=("relativo", "mean"),
                    tiendas=("tiendas", "max"), **{c: (c, "first") for c in LINAJE})
               .reset_index())
    cadenas["indice"] = cadenas["indice"].round(1)
    cadenas["mas_barata_en"] = cadenas["cadena_comercial"].map(mas_barata).fillna(0).astype(int)
    return comparativo, cadenas.sort_values("indice").reset_index(drop=True)[COLUMNAS_CADENA]
