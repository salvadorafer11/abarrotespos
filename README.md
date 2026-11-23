# AbarrotesPOS · TRUSTED DATA LAB

**¿Qué vende mi tienda, cuándo vende más (quincena, fin de semana, eventos, calor) y a qué precio me conviene vender comparado con el mercado y con la competencia de mi colonia?**

Proyecto Integrador TRUSTED DATA LAB (TecNM campus Colima): Ingeniería de Datos, Análisis Estadístico para Ciencia de Datos y Calidad en los Sistemas de Información.

- **Cliente piloto:** Abarrotes "El Amiguito", col. General Manuel Álvarez, Villa de Álvarez (propuesto por el profe Mónico el 20-nov; visita pendiente).
- **Modelo de negocio:** renta mensual del sistema a tiendas de barrio (precio a validar con el cliente; el profe pide al menos una venta real).
- **Equipo:** Ángel Salvador Álvarez Fernández (Análisis, líder) · Julio Alberto Orozco Téllez (Ingeniería de Datos) · José Rey Sánchez Navarro (Calidad).
- **Por qué dejamos ObraPrecio:** [docs/E2/pivote-abarrotespos.md](docs/E2/pivote-abarrotespos.md). El repo anterior (E0 y E1) queda intacto en [tdl-observatorio-electrico](https://github.com/23460521-commits/tdl-observatorio-electrico).
- **Entrega actual:** [E2 · ficha y pendientes](docs/E2/ENTREGA.md) · [tareas por integrante](docs/E2/TAREAS.md)

## Qué hace el sistema

| Módulo | Qué le da al dueño | Materia |
|---|---|---|
| Punto de venta (tickets, contado y fiado) | Registro de cada venta, control de fiados por cliente (clave anónima) | Ing. de Datos |
| Precios de mercado (PROFECO, centrales de abasto) | "Tu refresco está $2 arriba del promedio de Colima" | Ing. de Datos |
| Competencia en el mapa (OpenStreetMap / DENUE) | Cuántas tiendas hay a 500 m y dónde | Ing. de Datos (fuente especializada E2) |
| Estadística de ventas | Cuánto vendió, cuánto ganó, qué producto deja más, picos por quincena, día y evento, efecto del clima | Análisis |
| Pronóstico | Cuánto surtir para la próxima semana / evento | Análisis (E3) |
| Calidad | Puerta de datos, pruebas, CI, fiabilidad, ISO/IEC 25010 y 25012 | Calidad |

## Fuentes

| Fuente | Qué aporta | Acceso | Estado |
|---|---|---|---|
| Ventas del POS | Tickets de la tienda | Propias (con permiso del dueño) | **Demo sintética** (`pos_demo`) hasta tener las reales (`pos_cliente`) |
| Open-Meteo | Temperatura y lluvia diaria en la tienda | API sin llave, CC BY 4.0 | Extractor listo (`extractores/clima.py`) |
| OpenStreetMap (Overpass) | Comercios de abarrotes en Colima y Villa de Álvarez | API sin llave, ODbL | Extractor listo (`extractores/tiendas_osm.py`) |
| INEGI DENUE | Tiendas con giro SCIAN 461110 y coordenadas | API con token gratuito | Pendiente (Julio) |
| PROFECO "Quién es Quién en los Precios" | Precios de la canasta en tiendas de Colima | Datos abiertos | Pendiente (Julio) |

## Capas

```
fuentes -> data/bronce (respuesta exacta + .meta.json con SHA-256)
        -> puerta de calidad (Pandera) -> data/cuarentena (rechazados con motivo)
        -> data/plata (limpio) -> data/oro (análisis; cada fila con fuente, archivo_bronce, capturado_utc)
```

## Cómo correrlo

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pipeline.ejecutar              # bronce -> plata -> oro
python -m extractores.clima              # captura clima (red)
python -m extractores.tiendas_osm        # captura comercios OSM (red)
python -m pytest -q && ruff check .
streamlit run tablero/app.py
python -m laboratorio.experimento_factorial correr --replicas 3   # experimento E2
```

## Reglas fijas

Cero datos personales (los fiados usan claves F001…, nunca nombres ni teléfonos). Scraping con robots.txt, User-Agent honesto y ≥ 1 s entre peticiones. Los tokens viven en GitHub Secrets. La IA generativa se usa y se declara en cada relatoría.
