# E2 · Tareas por integrante (lunes 23-nov-2026)

**Hora límite del equipo: 17:30** para tener todo en `main`; Ángel pone la etiqueta `e2` a las 17:45 (la plataforma cierra 17:59).
Revisiones en el grupo: **11:00**, **14:00** y **16:30** (cada quien manda qué lleva y qué le falta).

Reglas para todos:
- Trabajar en una rama propia (`julio-datos`, `jose-calidad`, `angel-analisis`) y abrir Pull Request a `main`. Si el CI sale en rojo, no se une.
- Antes de cada PR: `ruff check .` y `python -m pytest -q` en verde.
- Anotar tu tiempo en `calidad/tiempo-<tu-nombre>.csv` y cada error que corrijas en `calidad/defectos-<tu-nombre>.csv`.
- Si usas IA (Claude, ChatGPT, Codex), lo dices en la relatoría: qué herramienta y para qué. Lo que no puedas explicar en la defensa no cuenta.
- Cero datos personales: nada de nombres, teléfonos o correos de personas.

---

## Julio · Ingeniería de Datos (90 pts de la rúbrica E2)

| # | Tarea | Archivo | Pts | Listo cuando |
|---|---|---|---|---|
| J1 | **Fuente especializada geoespacial**: correr `python -m extractores.tiendas_osm`, revisar que bronce tenga las tiendas, correr el pipeline y ver el mapa en el tablero | `extractores/tiendas_osm.py`, `data/bronce/osm_overpass/` | 45 | El mapa sale en `streamlit run tablero/app.py` con el conteo de tiendas a 500 m |
| J2 | Unión espacial con GeoPandas (lo pide la rúbrica): tiendas OSM dentro de un radio de 500 m de la tienda piloto (`sjoin` o `buffer`), en EPSG:6372 (metros) | `pipeline/geo.py` nuevo | (parte de J1) | `data/oro/competencia_tienda_piloto.csv` sale de GeoPandas |
| J3 | Poner las coordenadas reales de "El Amiguito" (Google Maps, clic derecho → copiar coordenadas) en `TIENDA_LAT` / `TIENDA_LON` de `extractores/config.py` | `extractores/config.py` | — | `coordenadas_confirmadas = True` |
| J4 | **Declaración de ética y legalidad**: completar cada fila (base legal, términos, licencia, privacidad, sesgos, mitigación) | `docs/etica-datos.md` | 30 | Ninguna celda dice "PENDIENTE" |
| J5 | **Linaje**: comprobar con 3 ejemplos que una fila de oro se rastrea hasta su `.meta.json` y SHA-256 | `docs/linaje.md` nuevo | 15 | 3 ejemplos con capturas o comandos |
| J6 | Precios de mercado PROFECO QQP (si da tiempo; si no, queda para E3) | `extractores/precios_profeco.py` | extra | Archivo en bronce con su meta |
| J7 | **Visita a la tienda**: platicar con el dueño usando el guion | `docs/cliente/guion-entrevista.md` | — | Respuestas anotadas, sin datos personales del dueño |

Si OSM falla desde tu red, alternativa: DENUE de INEGI (token gratuito en https://www.inegi.org.mx/servicios/api_denue.html, giro SCIAN 461110). El token va en GitHub Secrets como `DENUE_TOKEN`, nunca en el código.

---

## Ángel · Análisis Estadístico (90 pts)

| # | Tarea | Archivo | Pts | Listo cuando |
|---|---|---|---|---|
| A1 | Correr el **2³** completo con 3 réplicas en orden aleatorio: `python -m laboratorio.experimento_factorial correr --replicas 3` | `laboratorio/resultados/corridas_2k3.csv` | 25 | 24 corridas guardadas |
| A2 | **Bloqueo**: repetir A1 en una segunda máquina (`MAQUINA=pc-angel` y `MAQUINA=pc-julio`, o la nube de GitHub) para que el bloque entre al ANOVA | mismo archivo | (A1) | Dos valores en la columna `bloque` |
| A3 | **Dos factores con 3 niveles**: `... dos-factores --replicas 3` (tamaño chico/mediano/grande × formato) e interpretar la interacción | `corridas_dos_factores.csv` | 20 | ANOVA de dos vías interpretado |
| A4 | **Completo vs fraccionado**: `... matrices` ya generó 2⁴ (16) y 2⁴⁻¹ con D = ABC (8, ahorro 50 %, resolución IV). Explicar los alias | `matriz_*.csv`, `alias_2k4-1.csv` | 20 | Tabla de alias explicada en el cuaderno |
| A5 | **Análisis**: `... analizar` → ANOVA, efectos, gráficas de interacción, residuos (Shapiro, Levene) | `anova_2k3.csv`, `interacciones.png`, `residuos.png` | 25 | Conclusión con números |
| A6 | **Confirmación del óptimo**: `... confirmar --corridas 5` | `confirmacion.csv` | (A5) | "La mejor combinación es X y mejora Y %" |
| A7 | Cuaderno que explica todo lo anterior | `laboratorio/experimento_E2.ipynb` | — | Corre de principio a fin |
| A8 | Relatoría de etapa (con lo que manden Julio y José Rey) y etiqueta `e2` | `docs/relatoria-E2.md` | 10 en cada materia | Las 6 preguntas, con fechas y números |

---

## José Rey · Calidad (90 pts)

| # | Tarea | Archivo | Pts | Listo cuando |
|---|---|---|---|---|
| R1 | **ISO/IEC 25010**: para las 8 características, la métrica ya está definida; medirla y calificarla | `docs/calidad/iso25010.md` | 30 | Cada fila con valor medido y evidencia (archivo o comando) |
| R2 | **ISO/IEC 25012** sobre la capa oro: exactitud, completitud, consistencia, credibilidad, actualidad y las demás | `docs/calidad/iso25012.md` | 25 | Cada fila con su número sacado de `data/oro/` |
| R3 | **Antecedentes normativos**: cuadro ISO/IEC 9126 → familia 25000 (SQuaRE) y la ISO 9001 vigente con enfoque a procesos | `docs/calidad/antecedentes-normativos.md` | 10 | Cuadro completo, sin confundir normas |
| R4 | **Auditoría cruzada** del equipo asignado (estado E1) con hallazgos crítico/mayor/menor, evidencia y recomendación | `docs/calidad/auditoria-cruzada.md` | 25 | Al menos 6 hallazgos con evidencia |
| R5 | Actualizar el plan SQA al nuevo proyecto (nombres, alcance, riesgos) | `docs/plan-sqa.md` | — | Ya no dice ObraPrecio salvo en "antecedentes" |

Tip para Codex/ChatGPT: dale este archivo, `README.md` y la carpeta `docs/calidad/`, y pídele que te ayude a **medir**, no a inventar: cada número tiene que salir de correr un comando sobre el repo.
