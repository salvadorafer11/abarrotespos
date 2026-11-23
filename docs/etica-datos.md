# Declaración de ética y legalidad de datos · AbarrotesPOS

Responsable: Julio Alberto Orozco Téllez (Ingeniería de Datos). Versión E2: 23-nov-2026.

Marco general: Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP). Regla del proyecto: cero datos personales; scraping con robots.txt, User-Agent honesto y ≥ 1 s entre peticiones.

| Fuente | Base legal de uso | Términos / licencia | Riesgos de privacidad | Sesgos conocidos | Mitigación |
|---|---|---|---|---|---|
| Ventas del POS de la tienda piloto (`pos_cliente`) | Consentimiento informado del dueño del negocio, por escrito, para usar sus ventas solo para su tablero. Se pide en la visita (J7); **sin consentimiento no se carga ninguna venta real** y el sistema sigue con `pos_demo` | Datos propiedad del cliente; uso exclusivo para su tablero | Los fiados identifican a vecinos | Una sola tienda: no representa a todas | Fiados con clave anónima (F001…), nunca nombres ni teléfonos; no se publican tickets, solo agregados |
| Ventas de demostración (`pos_demo`) | Generadas por el equipo (sin personas) | Propias | Ninguno | Los supuestos (quincena +20 %, fin de semana +25 %, cabalgata ×1.8) son hipótesis del equipo | Se marcan como demo en oro y en el tablero; se reemplazan con datos reales |
| Open-Meteo | Datos abiertos | Datos CC BY 4.0 (atribución). La API gratuita es solo para uso no comercial: mientras sea proyecto escolar se usa gratis; **si el sistema se renta, se contrata el plan comercial de Open-Meteo** o se cambia a datos del SMN/CONAGUA | Ninguno | Modelo de reanálisis, no estación en la tienda | Se cita la fuente; se compara con estación SMN si hay dudas |
| OpenStreetMap (Overpass) | Datos abiertos; la consulta respeta robots.txt y la política de uso de Overpass (una consulta por captura, pausa ≥ 2 s) | ODbL 1.0: atribución y compartir igual las bases derivadas (`competencia_tienda_piloto.csv` se publica bajo ODbL con la atribución "© colaboradores de OpenStreetMap" que ya muestra el tablero) | Algunas etiquetas traen teléfono/correo/sitio | Cobertura incompleta: muchas tienditas de barrio no están mapeadas | Se eliminan las etiquetas de contacto antes de bronce (`ETIQUETAS_PROHIBIDAS`); se contrasta con DENUE |
| INEGI DENUE (alternativa; no se usa en E2 porque OSM respondió) | Información pública de interés nacional | Términos de libre uso de INEGI; token personal | Trae teléfono y correo de negocios (a veces de personas físicas) | Actualización periódica; negocios informales no aparecen | Se descartan teléfono, correo y razón social de personas físicas en bronce; token en GitHub Secrets |
| PROFECO QQP (planeada para E3) | Datos abiertos (datos.gob.mx) | Licencia de Libre Uso MX | Ninguno (precios de establecimientos) | Solo cadenas y tiendas encuestadas por PROFECO, no tienditas | Se usa como referencia de mercado, no como precio de la competencia directa |

## Uso secundario y venta del sistema
Si el sistema se renta a otras tiendas, los datos de cada tienda solo los ve su dueño. No se venden ni se cruzan datos entre clientes sin su permiso por escrito.

## robots.txt y APIs públicas (decisión del equipo, 23-nov-2026)
Al correr la captura, Overpass y Open-Meteo respondieron que su `robots.txt` no permite las rutas `/api/`. Ese archivo está dirigido a **rastreadores web** (buscadores que recorren páginas); las dos son **APIs públicas documentadas para consumo por programa**. Decisión: para esos dos hosts (`APIS_CON_TERMINOS` en `extractores/config.py`) se siguen sus **términos de uso** en lugar de `robots.txt`: User-Agent con contacto, pausa ≥ 1.5 s, una sola consulta por captura y la liga a los términos en cada `.meta.json`. **Cualquier otro sitio sigue sujeto a `robots.txt` sin excepción** (prueba `test_api_con_terminos_pasa_y_sitio_comun_respeta_robots`).

## Ubicación de la tienda piloto
Las coordenadas de `extractores/config.py` son las del **local comercial** (dato público: cualquiera lo ve en la calle y en Google Maps), no del domicilio de una persona. Se toman con permiso del dueño en la visita; si el dueño no quiere que aparezca su tienda en el mapa del repositorio público, se redondean a 3 decimales (~100 m).

## Linaje y auditoría
Cada fila de `data/oro/` trae `fuente`, `archivo_bronce` y `capturado_utc`. Con `python -m pipeline.linaje <archivo_oro> <fila>` se comprueba que el SHA-256 del archivo de bronce coincide con su `.meta.json` (ver [linaje.md](linaje.md)).

## Uso de IA generativa
Se usó Claude (Anthropic) para escribir `pipeline/geo.py`, `pipeline/linaje.py`, el mapa del tablero y el borrador de este documento. Julio revisó, corrió y puede explicar cada parte.
