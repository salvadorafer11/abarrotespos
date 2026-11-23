# Plan de Aseguramiento de la Calidad del Software (SQAP) · AbarrotesPOS

Estructura basada en IEEE Std 730. Versión 2.0 del 23 de noviembre de 2026.
Estado: **borrador del responsable de Calidad (José Rey Sánchez Navarro) para la entrega E2; pendiente de revisión del líder.**

## 0. Antecedentes
Este plan nace del SQAP v1.2 (13-nov-2026) del proyecto anterior del equipo, **ObraPrecio** (costo de construcción de vivienda con datos de INEGI y Banxico), calificado en E0 y E1 en el repositorio [tdl-observatorio-electrico](https://github.com/23460521-commits/tdl-observatorio-electrico). En E2 el equipo cambió de tema ([por qué](E2/pivote-abarrotespos.md)) y se trajeron el extractor ético, la capa bronce con SHA-256, la puerta de calidad con cuarentena, el CI y este plan como base.

De ObraPrecio se conserva sólo lo que aplica como práctica (independencia de la revisión, lista de revisión de entrega, registro PSP). **Sus métricas y cifras no se trasladan**: todos los valores de la sección 5.2 se miden de nuevo sobre AbarrotesPOS. Sus 9 defectos quedan como historia en `calidad/defectos-heredados-obraprecio.csv`.

## 1. Propósito y alcance
Este plan define cómo el equipo asegura la calidad de **AbarrotesPOS**, el módulo del TRUSTED DATA LAB que responde a la tienda de barrio: qué vende, cuándo vende más (quincena, fin de semana, eventos, calor) y a qué precio le conviene vender frente al mercado y a la competencia de su colonia. Cliente piloto: Abarrotes "El Amiguito" (Villa de Álvarez, Colima).

Cubre todo lo que vive en el repositorio:
- Punto de venta: tickets de contado y fiado (hoy **demo sintética** `pos_demo`; ventas reales `pos_cliente` cuando el dueño las autorice).
- Extractores: Open-Meteo (clima), OpenStreetMap/Overpass (comercios); INEGI DENUE y PROFECO QQP planeados.
- Pipeline bronce → puerta de calidad (Pandera) → plata / cuarentena → oro, con linaje.
- Laboratorio estadístico (`laboratorio/experimento_factorial.py`), tablero Streamlit (`tablero/app.py`), flujos de GitHub Actions y la documentación.

Queda fuera en E2: pronóstico de surtido (E3) y cualquier dato personal de clientes (los fiados usan claves `F001…`).

## 2. Documentos de referencia
- IEEE Std 730, Software Quality Assurance Processes.
- ISO/IEC 25010:2023 (calidad del producto) e ISO/IEC 25012:2008 (calidad de datos); antecedentes en [antecedentes-normativos.md](calidad/antecedentes-normativos.md).
- ISO 9001:2026, sistemas de gestión de la calidad (enfoque a procesos, PHVA).
- [README](../README.md), [ficha E2](E2/ENTREGA.md), [tareas E2](E2/TAREAS.md), [cambio de tema](E2/pivote-abarrotespos.md).
- [Ética y legalidad de datos](etica-datos.md), [guion de entrevista al cliente](cliente/guion-entrevista.md).
- Evaluaciones: [ISO/IEC 25010](calidad/iso25010.md), [ISO/IEC 25012](calidad/iso25012.md), [auditoría cruzada](calidad/auditoria-cruzada.md).

## 3. Gestión
### 3.1 Organización y responsabilidades
| Rol | Persona | Responsabilidad |
|---|---|---|
| Responsable de Calidad | José Rey Sánchez Navarro | Mantiene este plan, mide ISO/IEC 25010 y 25012, hace la auditoría cruzada, revisa cada entrega contra la sección 6 |
| Líder del proyecto (Análisis) | Ángel Salvador Álvarez Fernández | Prioriza, coordina con docentes y cliente, aprueba la entrega, pone la etiqueta y escribe la relatoría |
| Ingeniería de Datos | Julio Alberto Orozco Téllez | Extractores, pipeline, linaje, ética de fuentes, secretos y flujos de GitHub Actions |
| Todo el equipo | | Rama propia y Pull Request a `main`; registrar tiempo y defectos; no unir con el CI en rojo |

Independencia: quien revisa una entrega no es quien escribió el cambio principal. Cuando el código o los documentos se generan con IA, la revisión humana de la sección 6 es obligatoria y el uso se declara en la relatoría.

### 3.2 Tareas de calidad por etapa
| Etapa | Tareas de SQA | Estado |
|---|---|---|
| E2 (23-nov) | Plan SQA actualizado, evaluación ISO/IEC 25010 y 25012 con mediciones, antecedentes normativos, auditoría cruzada, registros PSP por integrante | En curso |
| E3 | Pruebas de aceptación con el dueño de la tienda, fiabilidad con bitácora de varios días, cobertura de pruebas, prueba automatizada del tablero | Planeado |

## 4. Documentación
| Documento | Dónde | Quién lo mantiene |
|---|---|---|
| README y fichas de entrega | `README.md`, `docs/E*/ENTREGA.md` | Líder |
| Tareas por integrante | `docs/E2/TAREAS.md` | Líder |
| Relatorías | `docs/relatoria-E*.md` | Líder |
| Este plan y evaluaciones de calidad | `docs/plan-sqa.md`, `docs/calidad/` | Calidad |
| Ética y legalidad por fuente | `docs/etica-datos.md` | Datos |
| Linaje | columnas `fuente`, `archivo_bronce`, `capturado_utc` en oro; `docs/linaje.md` | Datos |
| Contrato de datos | `ESQUEMA_VENTAS` en `pipeline/ejecutar.py` (Pandera) | Datos |
| Experimento | `laboratorio/experimento_E2.ipynb`, `laboratorio/resultados/` | Análisis |

Regla: toda cifra escrita en un documento debe poder regenerarse con un comando del repositorio.

## 5. Estándares, prácticas, convenciones y métricas
### 5.1 Estándares y convenciones
- Python 3.11, estilo verificado con `ruff` (líneas de hasta 100 caracteres, reglas E, F, W, I, UP, B; ver `pyproject.toml`).
- Nombres de código, datos y documentos en español.
- Trabajo en ramas `julio-datos`, `jose-calidad`, `angel-analisis`; integración sólo por Pull Request con CI en verde.
- Datos: la capa bronce nunca se modifica; plata y oro se regeneran desde bronce con `python -m pipeline.ejecutar`.
- Ética de fuentes: robots.txt, User-Agent honesto con contacto, al menos 1 s entre peticiones; tokens sólo en GitHub Secrets.
- Cero datos personales: fiados con claves anónimas; sin nombres, teléfonos ni correos.

### 5.2 Métricas y objetivos
Los valores medidos y su evidencia viven en [iso25010.md](calidad/iso25010.md) e [iso25012.md](calidad/iso25012.md); aquí sólo el resumen.

Medido el 23-nov-2026 en Windows 11, Python 3.15.2 (rama `jose-calidad`, commit base `256d4f5`).

| Métrica | Cómo se mide | Objetivo | Valor E2 |
|---|---|---|---|
| Pruebas automáticas que pasan | `python -m pytest -q` | 100 % | 6 de 6 (100 %); 27 advertencias de pandas |
| Errores de estilo | `ruff check .` | 0 | 0 |
| Complejidad ciclomática promedio | `radon cc -a` | A–B | A (3.49); 1 función en C |
| Secretos expuestos | gitleaks (job `seguridad` del CI) | 0 | Pendiente de la ejecución del Pull Request |
| Dependencias vulnerables | `pip-audit -r requirements.txt` | 0 | 0 |
| Ventas aceptadas por la puerta | `calidad/reporte-puerta.json`: plata / (plata + cuarentena) | Se reporta | 100 % (137 867 de 137 867; datos de demostración) |
| Filas de oro con linaje completo | `python calidad/medir_iso25012.py` | 100 % | 100 % (1 299 de 1 299; SHA-256 de bronce verificado) |
| Columnas con datos personales en oro | Igual | 0 | 0 (0 correos y 0 teléfonos en 9 042 celdas) |
| Disponibilidad de la captura `A = MTBF / (MTBF + MTTR)` | `calidad/bitacora-captura.csv` | ≥ 95 % | No medible: 0 días de bitácora |
| Mejora de desempeño del óptimo del experimento | `python calidad/medir_iso25010.py --confirmacion …` | ≥ 30 % | 82.1 % (datos de la rama `angel-analisis`) |
| Defectos registrados y cerrados | `calidad/defectos-<nombre>.csv` | 100 % cerrados o listados como abiertos antes de etiquetar | Calidad: 5 registrados, 5 corregidos (al 23-nov, 15:01) |

Detalle y evidencia: [iso25010.md](calidad/iso25010.md) e [iso25012.md](calidad/iso25012.md).

## 6. Revisiones y auditorías
| Revisión | Cuándo | Quién | Criterio de salida |
|---|---|---|---|
| Revisión de cambio | Cada Pull Request y cada push a `main` | CI (`.github/workflows/ci.yml`) | ruff, pytest, pipeline y seguridad en verde |
| Revisión de entrega | Antes de la etiqueta | Responsable de Calidad | Lista siguiente completa |
| Auditoría de datos | Cada corrida del pipeline | Puerta de calidad (Pandera) | Plata no vacía; rechazados en cuarentena con motivo |
| Auditoría cruzada | E2 (19 al 23 de noviembre) | Calidad hacia otro equipo y viceversa | Hallazgos con evidencia y severidad ([auditoria-cruzada.md](calidad/auditoria-cruzada.md)) |
| Revisión posterior a un incidente | Tras una falla de captura | Calidad y Datos | Defecto registrado con causa y corrección |

**Lista de revisión de entrega**
1. El CI del commit a etiquetar está en verde.
2. `docs/E2/ENTREGA.md` enlaza evidencia existente para cada criterio de la rúbrica.
3. Las cifras de los documentos coinciden con `calidad/reporte-puerta.json`, `data/oro/` y `laboratorio/resultados/`.
4. Lo que no se hizo está escrito como pendiente o limitación (por ejemplo, ventas aún sintéticas).
5. No hay secretos ni datos personales (gitleaks en verde y revisión visual de archivos nuevos).
6. Los defectos de la etapa están registrados y cerrados, o listados como abiertos.
7. La relatoría describe el reparto real del trabajo y el uso de IA.

## 7. Pruebas
| Nivel | Qué cubre | Dónde | Cantidad en E2 |
|---|---|---|---|
| Unitarias | Demo reproducible y sin nombres, puerta y cuarentena, linaje en oro, limpieza de contactos OSM, distancia haversine, alias del fraccionado | `tests/test_basico.py` | 6 (todas pasan) |
| Datos (contrato) | Esquema Pandera de ventas (14 columnas, `strict`) y revisión "no vender abajo del costo" | `pipeline/ejecutar.py` | 1 esquema |
| Sistema | Pipeline completo en GitHub Actions | `.github/workflows/ci.yml` | En cada push y PR |
| Tablero | Carga del tablero con los datos de oro, sin navegador | `streamlit.testing` dentro de `calidad/medir_iso25010.py` | 1 revisión: 0 excepciones (fuera de `pytest`) |
| Aceptación | Tareas del dueño en el tablero | Prueba con el dueño (ver ISO/IEC 25010, capacidad de interacción) | Pendiente de la visita |

Las pruebas no usan internet. La cobertura de código todavía no se mide (E3).

## 8. Reporte de problemas y acción correctiva
1. Quien detecta un defecto lo registra en `calidad/defectos-<nombre>.csv` (tipo, fase en que se introdujo, fase en que se eliminó, minutos de corrección; formato PSP). El tiempo va en `calidad/tiempo-<nombre>.csv`.
2. Si afecta datos ya publicados, se abre además un issue en GitHub.
3. La corrección incluye una prueba que falle sin el arreglo, cuando sea posible.
4. Un registro inválido no es un defecto del código: va a `data/cuarentena/` con su motivo. Si el motivo se repite, se abre un defecto para revisar la regla o el extractor.
5. Una falla de la captura programada (`captura.yml`) deja la ejecución en rojo y una fila en la bitácora; Datos la atiende en menos de 24 h.

## 9. Herramientas, técnicas y metodologías
| Herramienta | Uso |
|---|---|
| Git y GitHub | Control de versiones, ramas por integrante, Pull Requests, etiquetas |
| GitHub Actions | CI y captura programada |
| pytest / ruff / radon | Pruebas, estilo y complejidad |
| Pandera | Contrato de datos (puerta de calidad) |
| gitleaks / pip-audit | Secretos en el historial y dependencias vulnerables |
| pandas, statsmodels, scipy | Pipeline y análisis estadístico |
| Streamlit | Tablero |
| PSP (registros de tiempo y defectos) | Medición del proceso personal |
| IA generativa (Claude, ChatGPT, Codex) | Borradores y código, siempre con revisión humana y verificación automática; se declara en la relatoría |

## 10. Control de medios y de configuración
- El repositorio de GitHub es la única fuente de verdad; cada entrega queda fija con una etiqueta (`e2`, `e3`).
- La capa bronce guarda la respuesta original comprimida con su `.meta.json` (SHA-256, fecha de captura, User-Agent).
- Los secretos (`DENUE_TOKEN`) viven en GitHub Secrets; `TDL_CONTACTO` es una variable del repositorio.
- `data/plata/ventas.csv` no se versiona (≈17 MB) y se reconstruye desde bronce.
- El historial de `main` no se reescribe.

## 11. Control de proveedores
| Proveedor | Qué entrega | Riesgo | Control |
|---|---|---|---|
| Tienda piloto (POS) | Tickets de venta | Datos incompletos o con información personal | Puerta Pandera, claves anónimas, permiso del dueño |
| Open-Meteo | Clima diario | Caída del servicio o cambio de formato | Bitácora de captura, CI en rojo, licencia CC BY 4.0 citada |
| OpenStreetMap / Overpass | Comercios de la zona | Servicio saturado, datos incompletos, contactos en las etiquetas | Reintentos y pausa; se quitan contactos (prueba `test_osm_quita_contactos`); licencia ODbL |
| INEGI DENUE / PROFECO QQP | Comercios con giro SCIAN; precios de mercado | Token vencido o cambio del conjunto de datos | Token en Secrets; validación de forma en el extractor |
| GitHub | Alojamiento y ejecución | Flujos programados retrasados u omitidos | Disponibilidad medida por día |
| Bibliotecas de Python | pandas, pandera, statsmodels, etc. | Vulnerabilidades o cambios incompatibles | pip-audit en CI; versiones mínimas en `requirements.txt` |

## 12. Registros: recolección, mantenimiento y retención
Bitácoras de captura, reporte de la puerta, defectos, tiempos y evaluaciones viven en `calidad/` y `docs/calidad/` y se conservan en el historial de Git durante todo el proyecto.

## 13. Capacitación
José Rey no cursa Ingeniería de Datos ni Análisis Estadístico: Julio y Ángel le explican el pipeline por capas y el experimento antes de la revisión de entrega. Todo el equipo debe poder correr los comandos de "Cómo correrlo" del README y explicar en la defensa lo que hizo con IA.

## 14. Gestión de riesgos
| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Las ventas siguen siendo sintéticas (no hay datos reales del cliente) | Alta | Alto | Declararlo en cada evaluación; columna `fuente = pos_demo`; pedir los tickets en la visita |
| Visita al cliente pendiente o el dueño no acepta | Media | Alto | Guion de entrevista listo; buscar otra tienda de la zona |
| Coordenadas de la tienda sin confirmar (`coordenadas_confirmadas = False`) | Alta | Medio | Tarea J3; mientras tanto se advierte que la competencia a 500 m es aproximada |
| Overpass u Open-Meteo no responden | Media | Medio | Reintentos, bitácora, alternativa DENUE |
| Exposición de datos personales en fiados o en etiquetas de OSM | Baja | Alto | Claves anónimas, limpieza de contactos con prueba, revisión de la sección 6 |
| Plazo de E2 en un solo día con tres ramas | Alta | Alto | Revisiones de las 11:00, 14:00 y 16:30; hora límite 17:30 |
| Integrantes que no pueden explicar una parte hecha con IA | Media | Alto | Revisión humana obligatoria y sesión de estudio antes de la defensa |
| Poca historia de captura para calcular fiabilidad | Alta | Medio | Declararlo como limitación; recalcular en E3 |

## 15. Control de cambios de este plan
Los cambios se hacen por commit, con aprobación del responsable de Calidad, y se anotan aquí.

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0–1.2 | 2026-11-13 | Versiones del proyecto anterior (ver sección 0) |
| 2.0 | 2026-11-23 | Adaptación a AbarrotesPOS (tarea R5): nombre, alcance, responsables, proveedores, riesgos y métricas nuevas; las cifras de E1 se retiran |
