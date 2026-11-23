# Cambio de tema: de ObraPrecio a AbarrotesPOS

Fecha de decisión: 22 de noviembre de 2026. Registrado: 23 de noviembre de 2026.

## Qué pasó
1. **18-nov (sesión de Ángel con el profe Mónico).** El profe insistió en vincular el proyecto con el sector productivo: un sistema que alguien pague, aunque sea poco ("con que lo vendan a 50 pesos me doy por bien servido; a 10 personas son 500"). Señaló que en Colima la mayoría de las pymes tiene sistema de ventas pero **no tiene analítica**: cuánto vendió, qué producto sale más, cuántas cotizaciones cerró.
2. **20-nov (clase).** El profe revisó la lluvia de 20 ideas del equipo (págs. 2 y 3 del documento E2) y marcó como factibles a corto plazo las ideas 10, 15, 16, 17 y 18. Para la **idea 10 (control de pedidos, fiados y colectas en tiendas de abarrotes)** propuso un cliente concreto: Abarrotes "El Amiguito", en General Manuel Álvarez, por donde pasa la cabalgata (pico de ventas). Pidió agregar estadística por periodos y eventos, clima, pronóstico y precios de mercado traídos de internet.
3. **22-nov (equipo).** José Rey y Julio propusieron en el grupo un sistema de punto de venta y monitoreo de precios; Ángel lo unió con la idea 10 y lo dicho por el profe. Los tres votaron por cambiar.

## Por qué se deja ObraPrecio
- Necesita clientes muy específicos (constructoras, arquitectos) y más tiempo del que queda en el semestre.
- Observación de campo (entrevista 1, hermano de Ángel): a contratistas y albañiles no les conviene transparentar precios.
- AbarrotesPOS tiene clientes en cualquier colonia (mayor alcance) y un cliente piloto identificado.

## Qué se reutiliza
Del repositorio anterior se trajo el extractor ético (`extractores/base.py`: robots.txt, User-Agent, pausa, reintentos), la capa bronce con SHA-256 y bitácora (`extractores/bronce.py`), la integración continua (ruff, pytest, pipeline, pip-audit, gitleaks), el patrón de puerta de calidad con cuarentena y el plan SQA como base. E0 y E1 siguen calificados en su repositorio y etiquetas originales.

## Riesgos declarados
- Las ventas son **simuladas** hasta que el cliente comparta las reales; el tablero lo avisa.
- El experimento E2 se corre por la **ruta ingeniería** (sobre el propio pipeline), así no depende del cliente esta semana.
- Equipo de 3 cuando la regla dice máximo 2: pendiente confirmarlo con los docentes.
