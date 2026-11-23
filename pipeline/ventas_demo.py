"""Ventas de DEMOSTRACION del punto de venta (datos sinteticos, con semilla fija).

Mientras la tienda piloto no nos entregue sus ventas reales, el sistema se prueba con
tickets simulados que imitan el comportamiento de una tienda de barrio: mas venta en fin
de semana y en quincena, picos en eventos (cabalgata, fiestas), mas bebidas frias con calor
y una parte de las ventas a credito ("fiado").

Todo lo que sale de aqui lleva fuente = "pos_demo" para que NUNCA se confunda con datos
reales. Cuando lleguen los del cliente, entran con fuente = "pos_cliente" por el mismo
pipeline. Los clientes de fiado son claves anonimas (F001...), nunca nombres.
"""

import numpy as np
import pandas as pd

# producto, categoria, precio_venta, costo, ventas_base_por_dia, sensible_al_calor
CATALOGO = [
    ("Refresco cola 600 ml", "bebidas", 20.0, 14.5, 38, True),
    ("Refresco cola 2.5 L", "bebidas", 45.0, 34.0, 12, True),
    ("Agua natural 1 L", "bebidas", 14.0, 8.0, 20, True),
    ("Bolsa de hielo 5 kg", "bebidas", 30.0, 16.0, 6, True),
    ("Cerveza lata 355 ml", "bebidas", 22.0, 16.5, 25, True),
    ("Jugo 1 L", "bebidas", 32.0, 23.0, 5, False),
    ("Leche entera 1 L", "lacteos", 29.0, 24.5, 22, False),
    ("Yogur bebible 250 g", "lacteos", 14.0, 10.0, 8, False),
    ("Queso fresco 250 g", "lacteos", 45.0, 33.0, 6, False),
    ("Huevo blanco 1 kg", "basicos", 48.0, 40.0, 14, False),
    ("Tortilla de maiz 1 kg", "basicos", 24.0, 19.0, 30, False),
    ("Frijol bayo 1 kg", "basicos", 38.0, 30.0, 5, False),
    ("Arroz 1 kg", "basicos", 32.0, 25.0, 6, False),
    ("Aceite vegetal 1 L", "basicos", 45.0, 37.0, 5, False),
    ("Azucar estandar 1 kg", "basicos", 34.0, 28.0, 6, False),
    ("Sopa de pasta 200 g", "basicos", 12.0, 8.5, 10, False),
    ("Atun en lata 140 g", "basicos", 24.0, 18.0, 7, False),
    ("Pan de caja grande", "panaderia", 52.0, 43.0, 9, False),
    ("Pan dulce pieza", "panaderia", 10.0, 6.0, 25, False),
    ("Papas fritas 45 g", "botanas", 19.0, 13.5, 18, True),
    ("Galletas paquete", "botanas", 18.0, 12.5, 12, False),
    ("Dulces surtidos", "botanas", 5.0, 2.8, 40, False),
    ("Jabon de lavanderia 1 kg", "limpieza", 42.0, 33.0, 4, False),
    ("Papel higienico 4 rollos", "limpieza", 36.0, 28.0, 6, False),
    ("Cloro 1 L", "limpieza", 22.0, 15.0, 4, False),
]

# Eventos locales que mueven la venta (multiplicador). Se ajustan con la entrevista al cliente.
EVENTOS = {
    "cabalgata": 1.8,  # la cabalgata pasa frente a la tienda piloto (dato del profe, 20-nov)
    "fiestas_charrotaurinas": 1.4,
    "navidad": 1.3,
}


def _calendario_eventos(fechas):
    ev = pd.Series("", index=fechas)
    for f in fechas:
        if f.month == 2 and 1 <= f.day <= 14:
            ev[f] = "fiestas_charrotaurinas"
        if f.month == 2 and f.day == 2:
            ev[f] = "cabalgata"
        if f.month == 12 and 20 <= f.day <= 31:
            ev[f] = "navidad"
    return ev


def generar(desde="2025-01-01", hasta="2026-11-15", semilla=42, clima=None):
    """Devuelve un DataFrame con una fila por renglon de ticket."""
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range(desde, hasta, freq="D")
    eventos = _calendario_eventos(fechas)
    tmax = None
    if clima is not None and len(clima):
        tmax = clima.set_index("fecha")["temp_max_c"].reindex(fechas)
    filas = []
    ticket = 0
    for f in fechas:
        mult = 1.0
        mult *= 1.25 if f.dayofweek >= 5 else 1.0  # fin de semana
        mult *= 1.20 if f.day in (15, 16, 30, 31, 1) else 1.0  # quincena
        mult *= EVENTOS.get(eventos[f], 1.0)
        calor = 0.0
        if tmax is not None and not np.isnan(tmax.get(f, np.nan)):
            calor = max(0.0, tmax[f] - 30) * 0.05  # +5 % por grado arriba de 30 C
        for nombre, cat, precio, costo, base, sensible in CATALOGO:
            lam = base * mult * (1 + (calor if sensible else 0))
            piezas = rng.poisson(lam)
            # se reparte en tickets de 1 a 3 piezas
            while piezas > 0:
                n = int(min(piezas, rng.integers(1, 4)))
                piezas -= n
                ticket += 1
                fiado = rng.random() < 0.08
                hora = int(rng.choice([8, 9, 10, 12, 13, 14, 17, 18, 19, 20, 21]))
                filas.append((f"T{ticket:07d}", f, hora, nombre, cat, n, precio, costo,
                              "fiado" if fiado else "contado",
                              f"F{rng.integers(1, 41):03d}" if fiado else "", eventos[f]))
    df = pd.DataFrame(filas, columns=["ticket", "fecha", "hora", "producto", "categoria",
                                      "piezas", "precio_unitario", "costo_unitario",
                                      "forma_pago", "cliente_fiado", "evento"])
    df["fuente"] = "pos_demo"
    return df
