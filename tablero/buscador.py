"""Buscador de productos que tolera errores de dedo (búsqueda léxica difusa).

Por qué léxica y no vectorial: el catálogo es chico (25 productos) y los errores típicos son
de dedo ("asucar", "tortiya", "lehce"), que se resuelven midiendo cuántas letras cambian
(distancia de Damerau-Levenshtein). Una búsqueda vectorial necesitaría un modelo de
embeddings (dependencia pesada, o red) y no maneja bien esos errores en palabras sueltas. Lo
que sí aportaría, entender nombres comunes ("chesco", "papel de baño"), se cubre con una lista
de sinónimos y con las marcas que registra PROFECO para cada producto.

Cada producto es un "documento" con palabras de distinto peso: su nombre pesa más que sus
sinónimos, su descripción, sus marcas y su categoría. Para cada palabra de la consulta se toma
la palabra más parecida del documento; la calificación es el promedio.
"""

import re
import unicodedata

# Nombres comunes y marcas típicas (sin acentos; se normalizan igual que la consulta).
SINONIMOS = {
    "Refresco cola 600 ml": "chesco soda coca pepsi cola gaseosa",
    "Refresco cola 2.5 L": "chesco soda coca pepsi cola gaseosa familiar",
    "Agua natural 1 L": "agua purificada botella ciel epura bonafont",
    "Bolsa de hielo 5 kg": "hielo cubos",
    "Cerveza lata 355 ml": "chela birra cheve caguama tecate modelo indio",
    "Jugo 1 L": "jugo nectar naranja mango manzana durazno boing del valle jumex",
    "Leche entera 1 L": "leche lala alpura santa clara",
    "Yogur bebible 250 g": "yogurt yoghurt yogurth bebible",
    "Queso fresco 250 g": "queso panela fresco",
    "Huevo blanco 1 kg": "huevos blanquillos docena",
    "Tortilla de maiz 1 kg": "tortillas maiz",
    "Frijol bayo 1 kg": "frijoles pinto bayo",
    "Arroz 1 kg": "arroz blanco",
    "Aceite vegetal 1 L": "aceite cocina canola soya 123 nutrioli",
    "Azucar estandar 1 kg": "azucar morena estandar",
    "Sopa de pasta 200 g": "fideo fideos pasta sopita moderna",
    "Atun en lata 140 g": "atun lata dolores tuny",
    "Pan de caja grande": "pan blanco bimbo rebanado",
    "Pan dulce pieza": "concha bisquet cuerno dona panaderia",
    "Papas fritas 45 g": "sabritas botana frituras",
    "Galletas paquete": "galleta marias emperador",
    "Dulces surtidos": "dulce caramelo paleta chicle",
    "Jabon de lavanderia 1 kg": "detergente jabon polvo roma foca ariel",
    "Papel higienico 4 rollos": "papel bano sanitario rollos petalo regio",
    "Cloro 1 L": "blanqueador cloralex clorox",
}
VACIAS = {"de", "la", "el", "los", "las", "en", "con", "y", "a", "para", "un", "una", "del",
          "al", "o", "por"}
# Peso de cada campo del documento.
PESOS = {"nombre": 1.0, "sinonimos": 0.95, "descripcion": 0.9, "marcas": 0.85,
         "categoria": 0.8}
UMBRAL = 0.7  # calificación mínima (deja pasar dos errores en una palabra de 7 letras)
MARGEN = 0.12  # solo se muestran los que quedan cerca del mejor ("pan" no trae "panela")


def normalizar(texto):
    """Minúsculas, sin acentos y solo letras y números: 'Azúcar estándar' -> 'azucar estandar'."""
    sin_acentos = unicodedata.normalize("NFKD", str(texto))
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos.lower()).strip()


def palabras(texto):
    """Palabras útiles para buscar: sin vacías y sin letras sueltas (los números sí cuentan)."""
    return [p for p in normalizar(texto).split()
            if p not in VACIAS and (len(p) > 1 or p.isdigit())]


def distancia(a, b):
    """Distancia de Damerau-Levenshtein (alineación óptima): cuántas letras hay que cambiar,
    quitar, poner o intercambiar de lugar para pasar de `a` a `b`. 'lehce' -> 'leche' = 1."""
    filas = [list(range(len(b) + 1))]
    for i in range(1, len(a) + 1):
        fila = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            costo = 0 if a[i - 1] == b[j - 1] else 1
            fila[j] = min(filas[-1][j] + 1, fila[j - 1] + 1, filas[-1][j - 1] + costo)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                fila[j] = min(fila[j], filas[-2][j - 2] + 1)
        filas.append(fila)
    return filas[-1][-1]


def parecido(consulta, palabra):
    """De 0 a 1: qué tanto se parece una palabra de la consulta a una del documento. También
    cuenta el inicio de la palabra, para que 'azu' encuentre 'azucar' mientras se escribe."""
    if consulta == palabra:
        return 1.0
    if consulta.isdigit() or palabra.isdigit():
        return 0.9 if palabra.startswith(consulta) else 0.0
    completo = 1 - distancia(consulta, palabra) / max(len(consulta), len(palabra))
    if len(consulta) >= 3 and len(palabra) > len(consulta):
        inicio = 1 - distancia(consulta, palabra[:len(consulta)]) / len(consulta)
        completo = max(completo, 0.92 * inicio)
    return completo


def documento(clave, nombre, descripcion="", categoria="", marcas=()):
    """Palabras del producto con su peso (la más alta si una palabra sale en varios campos)."""
    campos = {"nombre": f"{clave} {nombre}", "sinonimos": SINONIMOS.get(clave, ""),
              "descripcion": descripcion, "marcas": " ".join(marcas), "categoria": categoria}
    pesos = {}
    for campo, texto in campos.items():
        for p in palabras(texto):
            pesos[p] = max(pesos.get(p, 0), PESOS[campo])
    return {"clave": clave, "palabras": pesos}


def hubo_correccion(consulta, doc):
    """True si alguna palabra de la consulta no está tal cual en el producto (ni como inicio de
    una de sus palabras): o sea, se encontró por parecido y vale preguntar "¿quisiste decir?"."""
    return any(p not in doc["palabras"] and not any(w.startswith(p) for w in doc["palabras"])
               for p in palabras(consulta))


def buscar(consulta, documentos, umbral=UMBRAL, margen=MARGEN):
    """[(clave, calificación)] de mayor a menor. Cada palabra de la consulta debe parecerse a
    alguna del producto (ninguna por debajo de 0.5), el promedio debe pasar el umbral y quedar
    a menos de `margen` del mejor resultado."""
    q = palabras(consulta)
    if not q:
        return []
    resultados = []
    for doc in documentos:
        mejores = [max((parecido(p, w) * peso for w, peso in doc["palabras"].items()),
                       default=0) for p in q]
        calificacion = sum(mejores) / len(mejores)
        if min(mejores) >= 0.5 and calificacion >= umbral:
            resultados.append((doc["clave"], round(calificacion, 3)))
    resultados.sort(key=lambda r: -r[1])
    return [r for r in resultados if r[1] >= resultados[0][1] - margen]
