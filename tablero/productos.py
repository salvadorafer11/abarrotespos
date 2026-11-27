"""Identidad visual de cada producto del catálogo: nombre con acentos, color y pictograma.

Cada producto tiene su propio dibujo (24 x 24, trazo de 1.5 como los iconos del tablero) y su
propio color. El dibujo es de dos tonos: el contorno en el color del producto y un relleno
suave (clase "a") en el mismo color al 22 %. Las claves son los nombres tal como vienen en
los datos (sin acentos); `nombre()` da el que se muestra.
"""

from urllib.parse import quote

# Relleno suave de los dibujos (segundo tono).
A = 'fill="currentColor" fill-opacity=".22" stroke="none"'

# clave en los datos -> (nombre para mostrar, color, elementos SVG)
PRODUCTOS = {
    "Refresco cola 600 ml": ("Refresco de cola 600 ml", "#DC2626", f"""
        <rect x="8.5" y="12" width="7" height="4.5" {A}/>
        <rect x="10" y="2" width="4" height="2" rx=".5"/>
        <path d="M10 4h4v1.5c0 1.2 1.5 2.3 1.5 4.5v10a2 2 0 0 1-2 2h-3a2 2 0 0 1-2-2V10
                 c0-2.2 1.5-3.3 1.5-4.5z"/>
        <path d="M8.5 12h7M8.5 16.5h7"/>"""),
    "Refresco cola 2.5 L": ("Refresco de cola 2.5 L", "#9F1239", f"""
        <rect x="6.5" y="11.5" width="11" height="5.5" {A}/>
        <rect x="9.5" y="1.5" width="5" height="2" rx=".5"/>
        <path d="M10 3.5h4v1.3c0 1.2 3.5 2.2 3.5 5.2v10.5a2 2 0 0 1-2 2h-7a2 2 0 0 1-2-2V10
                 c0-3 3.5-4 3.5-5.2z"/>
        <path d="M6.5 11.5h11M6.5 17h11M9 14.2c1-.8 2-.8 3 0s2 .8 3 0"/>"""),
    "Agua natural 1 L": ("Agua natural 1 L", "#0284C7", f"""
        <path d="M12 11.2c1.3 1.7 2.1 2.9 2.1 3.9a2.1 2.1 0 0 1-4.2 0c0-1 .8-2.2 2.1-3.9z" {A}/>
        <rect x="10" y="2.5" width="4" height="2.5" rx=".5"/>
        <path d="M9.6 5h4.8v1.2l1.6 2.3V20a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V8.5l1.6-2.3z"/>
        <path d="M12 11.2c1.3 1.7 2.1 2.9 2.1 3.9a2.1 2.1 0 0 1-4.2 0c0-1 .8-2.2 2.1-3.9z"/>"""),
    "Bolsa de hielo 5 kg": ("Bolsa de hielo 5 kg", "#0891B2", f"""
        <path d="M12 3.5 19.5 7.5 12 11.5 4.5 7.5z" {A}/>
        <path d="M12 3.5 19.5 7.5v9L12 20.5l-7.5-4v-9z"/>
        <path d="M4.5 7.5 12 11.5l7.5-4M12 11.5v9"/>
        <path d="M7.2 11.3v2.6M16.8 11.3v2.6"/>"""),
    "Cerveza lata 355 ml": ("Cerveza en lata 355 ml", "#B45309", f"""
        <rect x="7" y="10" width="10" height="5.5" {A}/>
        <path d="M7 5.5C7 4.5 9.2 4 12 4s5 .5 5 1.5V19c0 1-2.2 1.5-5 1.5S7 20 7 19z"/>
        <path d="M7 5.5c0 1 2.2 1.5 5 1.5s5-.5 5-1.5M7 10h10M7 15.5h10M11 5h2"/>"""),
    "Jugo 1 L": ("Jugo 1 L", "#EA580C", f"""
        <circle cx="12" cy="14.5" r="2.8" {A}/>
        <path d="M7 8.5h10V21H7zM7 8.5 8.8 6h6.4l1.8 2.5M15 6l1.8-3.5h2"/>
        <circle cx="12" cy="14.5" r="2.8"/>
        <path d="M12 11.7v5.6M9.2 14.5h5.6"/>"""),
    "Leche entera 1 L": ("Leche entera 1 L", "#2563EB", f"""
        <path d="M7 12h10v9H7z" {A}/>
        <path d="M7 9.5 9.5 4.5h5L17 9.5V21H7z"/>
        <path d="M7 9.5h10M9.5 4.5 12 9.5M7 12h10"/>
        <path d="M10 2.5h4"/>"""),
    "Yogur bebible 250 g": ("Yogur bebible 250 g", "#DB2777", f"""
        <path d="M7.7 12.5h8.6l-.5 5.5H8.2z" {A}/>
        <path d="M6 6.5h12V8H6z"/>
        <path d="M7 8h10l-1.2 12.1a1.6 1.6 0 0 1-1.6 1.4H9.8a1.6 1.6 0 0 1-1.6-1.4z"/>
        <path d="M7.7 12.5h8.6M9 4.5c1-1.3 2-2 3-2s2 .7 3 2"/>"""),
    "Queso fresco 250 g": ("Queso fresco 250 g", "#A16207", f"""
        <path d="M3 14.5 15 7l6 4z" {A}/>
        <path d="M3 14.5 15 7l6 4v6.5a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>
        <path d="M3 14.5h18"/>
        <circle cx="8" cy="17.3" r="1.1"/><circle cx="15" cy="16.8" r="1.3"/>
        <circle cx="12.5" cy="11.6" r=".7"/>"""),
    "Huevo blanco 1 kg": ("Huevo blanco 1 kg", "#92400E", f"""
        <ellipse cx="8.4" cy="13.2" rx="1.4" ry="2.4" {A}/>
        <path d="M10 21a5 5 0 0 1-5-5c0-4 2.4-9 5-9s5 5 5 9a5 5 0 0 1-5 5z"/>
        <path d="M14.3 7.8c.7-.9 1.5-1.4 2.2-1.4 2.3 0 4.5 4.2 4.5 7.8a4.6 4.6 0 0 1-6.2 4.3"/>"""),
    "Tortilla de maiz 1 kg": ("Tortilla de maíz 1 kg", "#D97706", f"""
        <ellipse cx="12" cy="8" rx="8.5" ry="3" {A}/>
        <ellipse cx="12" cy="8" rx="8.5" ry="3"/>
        <path d="M3.5 8v3c0 1.7 3.8 3 8.5 3s8.5-1.3 8.5-3V8M3.5 11v3c0 1.7 3.8 3 8.5 3s8.5-1.3
                 8.5-3v-3M3.5 14v3c0 1.7 3.8 3 8.5 3s8.5-1.3 8.5-3v-3"/>
        <circle cx="9" cy="7.6" r=".4"/><circle cx="14.5" cy="8.6" r=".4"/>"""),
    "Frijol bayo 1 kg": ("Frijol bayo 1 kg", "#7C2D12", f"""
        <ellipse cx="15.2" cy="15.6" rx="3.1" ry="4.4" transform="rotate(35 15.2 15.6)" {A}/>
        <ellipse cx="8.5" cy="9" rx="3.1" ry="4.4" transform="rotate(-30 8.5 9)"/>
        <ellipse cx="15.2" cy="15.6" rx="3.1" ry="4.4" transform="rotate(35 15.2 15.6)"/>
        <ellipse cx="7.8" cy="17.6" rx="2.2" ry="3.1" transform="rotate(70 7.8 17.6)"/>
        <path d="M8 7.6c.8.3 1.3 1.1 1.2 2M15.4 14.2c.6.6.8 1.5.4 2.3"/>"""),
    "Arroz 1 kg": ("Arroz 1 kg", "#475569", f"""
        <path d="M5 12c1-3.2 4-5 7-5s6 1.8 7 5z" {A}/>
        <path d="M3.5 12h17a8.5 8.5 0 0 1-17 0z"/>
        <path d="M5 12c1-3.2 4-5 7-5s6 1.8 7 5"/>
        <path d="M9 10l.8-.4M12 8.8h.9M14.6 10.1l.8.4M11 11l.8-.3"/>
        <path d="M9.5 20.5h5"/>"""),
    "Aceite vegetal 1 L": ("Aceite vegetal 1 L", "#65A30D", f"""
        <path d="M8.5 11h7v6.5h-7z" {A}/>
        <rect x="10" y="2" width="4" height="2.2" rx=".5"/>
        <path d="M10 4.2h4V7l1.5 2.5V20a2 2 0 0 1-2 2h-3a2 2 0 0 1-2-2V9.5L10 7z"/>
        <path d="M12 11.6c.9 1.2 1.5 2 1.5 2.8a1.5 1.5 0 0 1-3 0c0-.8.6-1.6 1.5-2.8z"/>"""),
    "Azucar estandar 1 kg": ("Azúcar estándar 1 kg", "#7C3AED", f"""
        <rect x="12.3" y="14.2" width="3.6" height="3.6" rx=".6" {A}/>
        <path d="M7.2 6.5h9.6l1.7 12.8a2 2 0 0 1-2 2.2H7.5a2 2 0 0 1-2-2.2z"/>
        <path d="M7.2 6.5c0-1.5 1.3-3 4.8-3s4.8 1.5 4.8 3M8.5 6.5c1 .8 2.2 1.2 3.5 1.2s2.5-.4
                 3.5-1.2"/>
        <rect x="8.4" y="12" width="3.6" height="3.6" rx=".6"/>
        <rect x="12.3" y="14.2" width="3.6" height="3.6" rx=".6"/>"""),
    "Sopa de pasta 200 g": ("Sopa de pasta 200 g", "#E11D48", f"""
        <path d="M3.5 11.5h17a8.5 8.5 0 0 1-17 0z" {A}/>
        <path d="M3.5 11.5h17a8.5 8.5 0 0 1-17 0z"/>
        <path d="M6.5 14.5c1-.9 2-.9 3 0s2 .9 3 0 2-.9 3 0 2 .9 3 0"/>
        <path d="M9 8.5c-.8-1-.8-2 0-3s.8-2 0-3M13 8.5c-.8-1-.8-2 0-3s.8-2 0-3M17 8.5c-.8-1
                 -.8-2 0-3"/>"""),
    "Atun en lata 140 g": ("Atún en lata 140 g", "#0E7490", f"""
        <ellipse cx="12" cy="9" rx="8.5" ry="3.2" {A}/>
        <ellipse cx="12" cy="9" rx="8.5" ry="3.2"/>
        <path d="M3.5 9v6.5c0 1.8 3.8 3.2 8.5 3.2s8.5-1.4 8.5-3.2V9"/>
        <path d="M8.6 9c1.4-1.2 3.4-1.2 4.8 0-1.4 1.2-3.4 1.2-4.8 0zM13.4 9l1.8-1v2z"/>"""),
    "Pan de caja grande": ("Pan de caja grande", "#C2410C", f"""
        <path d="M8.3 11a2.5 2.5 0 0 1 .9-4.6h5.6a2.5 2.5 0 0 1 .9 4.6V19H8.3z" {A}/>
        <path d="M6 10.2A4 4 0 0 1 7.9 3h8.2A4 4 0 0 1 18 10.2V20a1.5 1.5 0 0 1-1.5 1.5h-9A1.5
                 1.5 0 0 1 6 20z"/>
        <path d="M8.3 11a2.5 2.5 0 0 1 .9-4.6h5.6a2.5 2.5 0 0 1 .9 4.6V19H8.3z"/>"""),
    "Pan dulce pieza": ("Pan dulce (pieza)", "#BE185D", f"""
        <path d="M3.5 14.5a8.5 8.5 0 0 1 17 0z" {A}/>
        <path d="M3.5 14.5a8.5 8.5 0 0 1 17 0z"/>
        <path d="M3 14.5h18v1.7a1.8 1.8 0 0 1-1.8 1.8H4.8A1.8 1.8 0 0 1 3 16.2z"/>
        <path d="M8.2 14.3c0-3 1.4-5.6 3.8-6.8M15.8 14.3c0-3-1.4-5.6-3.8-6.8M5.2 11.2h13.6"/>"""),
    "Papas fritas 45 g": ("Papas fritas 45 g", "#CA8A04", f"""
        <path d="M9.4 12.2c1-2.1 4.1-2.6 5.1-1s-.4 4.1-2.5 4.6-3.6-1.5-2.6-3.6z" {A}/>
        <path d="M6 4l1.5 1.5L9 4l1.5 1.5L12 4l1.5 1.5L15 4l1.5 1.5L18 4v16l-1.5-1.5L15 20
                 l-1.5-1.5L12 20l-1.5-1.5L9 20l-1.5-1.5L6 20z"/>
        <path d="M9.4 12.2c1-2.1 4.1-2.6 5.1-1s-.4 4.1-2.5 4.6-3.6-1.5-2.6-3.6z"/>"""),
    "Galletas paquete": ("Galletas (paquete)", "#78350F", f"""
        <path d="M20 12a8 8 0 1 1-8-8 2.5 2.5 0 0 0 3 3 2.5 2.5 0 0 0 3 3 2 2 0 0 0 2 2z" {A}/>
        <path d="M20 12a8 8 0 1 1-8-8 2.5 2.5 0 0 0 3 3 2.5 2.5 0 0 0 3 3 2 2 0 0 0 2 2z"/>
        <circle cx="8.5" cy="10" r=".9"/><circle cx="13" cy="14.5" r=".9"/>
        <circle cx="8.8" cy="15.2" r=".9"/><circle cx="12" cy="9.8" r=".6"/>"""),
    "Dulces surtidos": ("Dulces surtidos", "#C026D3", f"""
        <circle cx="12" cy="12" r="4.5" {A}/>
        <circle cx="12" cy="12" r="4.5"/>
        <path d="M7.6 12 3.5 8.5v7zM16.4 12l4.1-3.5v7zM9.6 8.5l4.8 7M12.6 7.6l3 4.6"/>"""),
    "Jabon de lavanderia 1 kg": ("Jabón de lavandería 1 kg", "#0D9488", f"""
        <circle cx="9.5" cy="14.5" r="2.3" {A}/>
        <path d="M5 8.5h14V21H5zM5 8.5 7 4.5h10l2 4"/>
        <circle cx="9.5" cy="14.5" r="2.3"/><circle cx="14.4" cy="16.2" r="1.5"/>
        <circle cx="13.6" cy="11.8" r="1"/>"""),
    "Papel higienico 4 rollos": ("Papel higiénico 4 rollos", "#4F46E5", f"""
        <path d="M11 14.5h6.5v6.8l-1.6-1-1.6 1-1.7-1-1.6 1z" {A}/>
        <circle cx="7" cy="10" r="4.5"/><circle cx="7" cy="10" r="1.4"/>
        <path d="M7 5.5h10a4.5 4.5 0 0 1 0 9H7"/>
        <path d="M11 14.5v6.8l1.6-1 1.7 1 1.6-1 1.6 1v-6.8"/>"""),
    "Cloro 1 L": ("Cloro 1 L", "#16A34A", f"""
        <rect x="8.5" y="13" width="7" height="5" rx="1" {A}/>
        <rect x="9" y="2.5" width="4" height="2.5" rx=".5"/>
        <path d="M6 11 9 8.2V5h4v3.2l5 3.3v8A1.5 1.5 0 0 1 16.5 21h-9A1.5 1.5 0 0 1 6 19.5z"/>
        <path d="M13.2 8.4 16.7 6.3a1.5 1.5 0 0 1 2 .6l.4.8"/>
        <rect x="8.5" y="13" width="7" height="5" rx="1"/>"""),
}
GRIS = "#64748B"
_GENERICO = """<path d="M5 8h14l-1.2 11.2a2 2 0 0 1-2 1.8H8.2a2 2 0 0 1-2-1.8z"/>
               <path d="M9 8V6a3 3 0 0 1 6 0v2"/>"""


def nombre(producto):
    """Nombre para mostrar (con acentos); si no está en el catálogo, el mismo."""
    return PRODUCTOS.get(producto, (producto,))[0]


def color(producto):
    return PRODUCTOS.get(producto, (None, GRIS))[1]


def svg(producto, tono="currentColor"):
    dibujo = PRODUCTOS.get(producto, (None, None, _GENERICO))[2]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="{tono}" stroke-width="1.5" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">'
            + " ".join(dibujo.replace("currentColor", tono).split()) + "</svg>")


def ficha(producto, rango=None, tam=""):
    """Cuadro redondeado con el dibujo del producto en su color (y su lugar, si se pide)."""
    marca = f'<span class="rango">{rango}</span>' if rango is not None else ""
    return (f'<span class="ficha {tam}" style="--c:{color(producto)}" '
            f'title="{nombre(producto)}">{svg(producto)}{marca}</span>')


def imagen(producto):
    """El dibujo como data URI (para las gráficas de Altair, que no conocen currentColor)."""
    return "data:image/svg+xml;utf8," + quote(svg(producto, color(producto)))
