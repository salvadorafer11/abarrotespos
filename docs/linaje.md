# Linaje de datos · AbarrotesPOS (E2, tarea J5)

Responsable: Julio Alberto Orozco Téllez. Fecha: 23-nov-2026.

**Qué se demuestra:** cualquier fila de la capa oro se puede rastrear hasta el archivo crudo de bronce que la originó, y el SHA-256 guardado al capturar sigue coincidiendo con los bytes de ese archivo (nadie los alteró).

```
fuente ──► data/bronce/<fuente>/…/<nombre>.<ext>.gz  +  <nombre>.meta.json (sha256, capturado_utc, url, licencia)
              │ puerta de calidad (Pandera)
              ▼
         data/plata/*.csv ──► data/oro/*.csv  (cada fila: fuente, archivo_bronce, capturado_utc)
```

## Cómo se comprueba

```bash
python -m pipeline.ejecutar                                 # reconstruye plata y oro desde bronce
python -m pipeline.linaje data/oro/<tabla>.csv <fila>       # rastrea una fila
```

`pipeline/linaje.py` lee la fila de oro, busca su `archivo_bronce` dentro de `data/bronce/<fuente>/`, abre el `.meta.json`, descomprime el `.gz` y **vuelve a calcular el SHA-256**. La fila es íntegra si el hash recalculado y la fecha `capturado_utc` coinciden con los del `.meta.json`; si no, el comando termina con error `LINAJE ROTO`. La prueba `test_linaje_rastrea_oro_hasta_bronce` comprueba que alterar el `.meta.json` sí se detecta.

## Ejemplo 1 · Venta diaria → tickets del POS

```bash
python -m pipeline.linaje data/oro/ventas_diarias.csv 0
```
```json
{
  "oro": "data/oro/ventas_diarias.csv (fila 0)",
  "fuente": "pos_demo",
  "capturado_utc_en_oro": "2026-11-23T11:44:45.150073+00:00",
  "bronce": "data/bronce/pos_demo/demo/tickets_demo.csv.gz",
  "capturado_utc_en_meta": "2026-11-23T11:44:45.150073+00:00",
  "sha256_meta": "5f3bb5146ce4ae069cc532233a8e6f6bcdade82e815e7eea9fb06122bb92d5cb",
  "sha256_recalculado": "5f3bb5146ce4ae069cc532233a8e6f6bcdade82e815e7eea9fb06122bb92d5cb",
  "integro": true
}
```

## Ejemplo 2 · Producto del mes → tickets del POS

```bash
python -m pipeline.linaje data/oro/ventas_producto_mes.csv 0
```
Mismo archivo de bronce (`tickets_demo.csv.gz`), SHA-256 `5f3bb514…d5cb` recalculado e igual al del `.meta.json` → `"integro": true`. Muestra que dos tablas de oro distintas (agregado por día y por producto-mes) apuntan al mismo origen.

## Ejemplo 3 · Fiados por cliente (clave anónima) → tickets del POS

```bash
python -m pipeline.linaje data/oro/fiados_por_cliente.csv 0
```
→ `"integro": true`, mismo SHA-256. La fila de oro solo trae la clave `F0xx`: el linaje se comprueba sin exponer datos personales.

## Ejemplo 4 · Competencia a 500 m → captura de OpenStreetMap

```bash
python -m pipeline.linaje data/oro/competencia_tienda_piloto.csv 0
```
Esta fila sale de otra fuente (`osm_overpass`) y de otra unión (GeoPandas, `pipeline/geo.py`); su `archivo_bronce` es la captura `data/bronce/osm_overpass/AAAA-MM/tiendas_AAAA-MM-DD.json.gz`, con la consulta Overpass exacta y la licencia ODbL en su `.meta.json`.

## Notas
- Las ventas son **demostración** (`pos_demo`) hasta que el dueño de El Amiguito comparta las reales (`pos_cliente`); el linaje funciona igual con ambas.
- El SHA-256 se calcula sobre los bytes **originales** de la respuesta (antes de comprimir). El `.gz` se escribe con `mtime=0`, así el mismo contenido siempre produce el mismo archivo.
