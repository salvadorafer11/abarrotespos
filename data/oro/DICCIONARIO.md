# Diccionario de datos · capa oro

Responsable: José Rey Sánchez Navarro (Calidad), 23-nov-2026. Documentado a partir del código que genera cada tabla (`oro()` en `pipeline/ejecutar.py`; datos de demostración en `pipeline/ventas_demo.py`) y de los archivos de esta carpeta en el commit `256d4f5`. Los rangos se obtuvieron leyendo los CSV con pandas; se vuelven a comprobar con `python calidad/medir_iso25012.py`.

Convenciones de las tres tablas:
- Archivos CSV en UTF-8, separador coma, primera fila con encabezados.
- Importes en **pesos mexicanos (MXN)**, sin símbolo. El pipeline no redondea a centavos (ver la observación de precisión en `docs/calidad/iso25012.md`).
- Fechas en ISO 8601: `AAAA-MM-DD` (día), `AAAA-MM` (mes) y fecha-hora con zona UTC en `capturado_utc`.
- **Datos de demostración:** mientras `fuente = pos_demo`, todas las cifras son sintéticas (semilla 42), no ventas reales de la tienda.

## Columnas de linaje (presentes en las tres tablas)

| Columna | Tipo | Descripción | Valores en el commit `256d4f5` |
|---|---|---|---|
| `fuente` | texto | Origen de las ventas: `pos_demo` (sintéticas) o `pos_cliente` (reales de la tienda) | `pos_demo` |
| `archivo_bronce` | texto | Nombre del archivo crudo en `data/bronce/<fuente>/…` del que sale la fila; junto a él está su `.meta.json` con el SHA-256 | `tickets_demo.csv.gz` |
| `capturado_utc` | fecha-hora ISO 8601 con zona | Momento en que ese archivo entró a bronce (copiado del `.meta.json`) | `2026-11-23T11:44:45.150073+00:00` |

## `ventas_diarias.csv` · una fila por día (y evento)
Agrupa los renglones de ticket de plata por `fecha`, `evento` y linaje. 684 filas, del 2025-01-01 al 2026-11-15.

| Columna | Tipo | Descripción | Rango o valores |
|---|---|---|---|
| `fecha` | fecha `AAAA-MM-DD` | Día de la venta | 2025-01-01 a 2026-11-15 |
| `evento` | texto (vacío = día normal) | Evento local de ese día que mueve la venta | vacío, `cabalgata`, `fiestas_charrotaurinas`, `navidad` |
| `tickets` | entero | Tickets distintos del día | 155 a 429 |
| `piezas` | entero | Piezas vendidas en el día | 291 a 788 |
| `venta` | decimal (MXN) | Suma de `piezas × precio_unitario` | 6 421 a 18 539 |
| `ganancia` | decimal (MXN) | Suma de `piezas × (precio_unitario − costo_unitario)`; margen bruto, sin gastos de operación | 1 596.7 a 4 579 |
| `venta_fiado` | decimal (MXN) | Parte de `venta` con `forma_pago = fiado` (a crédito) | 194 a 1 604 |
| `dia_semana` | texto (inglés) | Nombre del día que da pandas (`day_name()`) | `Monday` … `Sunday` |
| `temp_max_c` | decimal (°C) | Temperatura máxima del día (Open-Meteo). **Sólo aparece si hay clima en plata**; ausente en el commit `256d4f5` | — |
| `lluvia_mm` | decimal (mm) | Lluvia del día (Open-Meteo). Misma condición que `temp_max_c` | — |

## `ventas_producto_mes.csv` · una fila por producto y mes
575 filas = 25 productos × 23 meses.

| Columna | Tipo | Descripción | Rango o valores |
|---|---|---|---|
| `mes` | texto `AAAA-MM` | Mes de la venta. **El último mes está incompleto** (los datos llegan al 15) | 2025-01 a 2026-11 |
| `producto` | texto | Producto del catálogo (25 en la demo) | p. ej. `Aceite vegetal 1 L` … `Yogur bebible 250 g` |
| `categoria` | texto | Familia del producto | `basicos`, `bebidas`, `botanas`, `lacteos`, `limpieza`, `panaderia` |
| `piezas` | entero | Piezas vendidas del producto en el mes | 61 a 1 532 |
| `venta` | decimal (MXN) | Suma de `piezas × precio_unitario` | 1 452 a 30 640 |
| `ganancia` | decimal (MXN) | Suma de `piezas × (precio_unitario − costo_unitario)` | 462 a 8 426 |

## `fiados_por_cliente.csv` · una fila por cliente de fiado
40 filas.

| Columna | Tipo | Descripción | Rango o valores |
|---|---|---|---|
| `cliente_fiado` | texto `F000` | **Clave anónima** del cliente a crédito; nunca nombre ni teléfono | `F001` a `F040` |
| `compras` | entero | Tickets distintos que el cliente pagó a fiado en todo el periodo | 235 a 319 |
| `adeudo_bruto` | decimal (MXN) | Suma de lo vendido a fiado. Es *bruto*: el POS no registra abonos, así que no es el saldo pendiente | 10 384 a 14 254 |
