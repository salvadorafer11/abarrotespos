# Declaración de ética y legalidad de datos · AbarrotesPOS

Responsable: Julio Alberto Orozco Téllez (Ingeniería de Datos). Borrador: 23-nov-2026. **Completar o corregir cada celda marcada PENDIENTE antes de etiquetar `e2`.**

Marco general: Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP). Regla del proyecto: cero datos personales; scraping con robots.txt, User-Agent honesto y ≥ 1 s entre peticiones.

| Fuente | Base legal de uso | Términos / licencia | Riesgos de privacidad | Sesgos conocidos | Mitigación |
|---|---|---|---|---|---|
| Ventas del POS de la tienda piloto (`pos_cliente`) | Consentimiento del dueño del negocio para usar sus ventas con fines de análisis (PENDIENTE: firmar aviso/consentimiento en la visita) | Datos propiedad del cliente; uso exclusivo para su tablero | Los fiados identifican a vecinos | Una sola tienda: no representa a todas | Fiados con clave anónima (F001…), nunca nombres ni teléfonos; no se publican tickets, solo agregados |
| Ventas de demostración (`pos_demo`) | Generadas por el equipo (sin personas) | Propias | Ninguno | Los supuestos (quincena +20 %, fin de semana +25 %, cabalgata ×1.8) son hipótesis del equipo | Se marcan como demo en oro y en el tablero; se reemplazan con datos reales |
| Open-Meteo | Datos abiertos | CC BY 4.0, uso no comercial gratuito (PENDIENTE: revisar condiciones si el sistema se renta) | Ninguno | Modelo de reanálisis, no estación en la tienda | Se cita la fuente; se compara con estación SMN si hay dudas |
| OpenStreetMap (Overpass) | Datos abiertos | ODbL 1.0: atribución y compartir igual las bases derivadas | Algunas etiquetas traen teléfono/correo/sitio | Cobertura incompleta: muchas tienditas de barrio no están mapeadas | Se eliminan las etiquetas de contacto antes de bronce (`ETIQUETAS_PROHIBIDAS`); se contrasta con DENUE |
| INEGI DENUE (PENDIENTE si se usa) | Información pública de interés nacional | Términos de libre uso de INEGI; token personal | Trae teléfono y correo de negocios (a veces de personas físicas) | Actualización periódica; negocios informales no aparecen | Se descartan teléfono, correo y razón social de personas físicas en bronce; token en GitHub Secrets |
| PROFECO QQP (PENDIENTE si se usa) | Datos abiertos (datos.gob.mx) | Licencia de Libre Uso MX | Ninguno (precios de establecimientos) | Solo cadenas y tiendas encuestadas por PROFECO, no tienditas | Se usa como referencia de mercado, no como precio de la competencia directa |

## Uso secundario y venta del sistema
Si el sistema se renta a otras tiendas, los datos de cada tienda solo los ve su dueño. No se venden ni se cruzan datos entre clientes sin su permiso por escrito.
