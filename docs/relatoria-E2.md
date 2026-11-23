# Relatoría E2 · AbarrotesPOS

Máximo dos páginas. Específica, honesta y verificable.

## 1. ¿Qué nos propusimos?

En la semana del 18 al 23 de noviembre: (a) cambiar de ObraPrecio a AbarrotesPOS con un cliente real (El Amiguito, Villa de Álvarez), (b) integrar al tablero una fuente geoespacial propia de la tienda y su zona, (c) encontrar con un diseño factorial 2³ la configuración del pipeline que procesa más rápido las ventas y cuánto mejora, y (d) evaluar producto y datos con ISO/IEC 25010 y 25012. Todo en el repositorio nuevo [salvadorafer11/abarrotespos](https://github.com/salvadorafer11/abarrotespos) (el anterior, [tdl-observatorio-electrico](https://github.com/23460521-commits/tdl-observatorio-electrico), queda intacto con E0 y E1).

## 2. ¿Qué hicimos? (de `calidad/tiempo-*.csv`)

| Fecha | Qué | Quién | Tiempo |
|---|---|---|---|
| 18-nov | Sesión con el profe Mónico: vinculación con pymes, idea de analítica de ventas | Ángel | — |
| 20-nov | Revisión de las 20 ideas: el profe marca factibles las 10, 15–18 y propone El Amiguito | Equipo | — |
| 22-nov | Decisión del grupo: cambio de tema a AbarrotesPOS | Equipo | — |
| 23-nov · 05:40 | Arranque del repo nuevo con esqueleto (pipeline, extractores, experimento) | Ángel (con IA) | — |
| 23-nov · 08:00–08:40 | Crear repo en GitHub, subir main, invitar colaboradores | Ángel | 40 min |
| 23-nov · 09:40–11:00 | Experimento factorial 2³ con 3 réplicas en dos bloques (nube y PC), ANOVA, confirmación | Ángel (con IA) | 80 min |
| 23-nov · 13:21–16:25 | Extractores OSM y clima, unión espacial 500 m, mapa, ética, verificador de linaje | Julio (con IA) | 184 min |
| 23-nov · 14:14–15:02 | Plan SQA v2.0, antecedentes normativos, ISO 25010 y 25012 con mediciones reproducibles | José Rey (con IA) | 48 min |

## 3. ¿Qué decidimos y por qué?

- **Cambiar de tema a AbarrotesPOS.** ObraPrecio exigía clientes muy específicos (cámaras de construcción); AbarrotesPOS tiene cliente piloto y mercado en cualquier colonia. Descartadas: seguir con ObraPrecio y las ideas 15–18 (campañas, aire acondicionado, dark kitchens, sucursales), por tiempo y porque el profe recomendó esta.
- **Ruta ingeniería en el experimento**, para no depender del cliente esta semana. Descartada: ruta negocio (precio vs. promoción), queda para E3 cuando haya ventas reales.
- **OpenStreetMap + Overpass** como fuente especializada, con DENUE como respaldo. Es sin token, sus términos permiten el uso académico y el extractor respeta sus límites.
- **Calidad con ISO/IEC 25010:2023** (producto) e **ISO/IEC 25012** (datos), ambas con script de medición reproducible (`calidad/medir_iso25010.py` y `medir_iso25012.py`) y evidencias en `calidad/mediciones/`.

## 4. ¿Qué salió mal y cómo lo corregimos? (de `calidad/defectos-*.csv`)

**10 defectos registrados, 0 abiertos.**

- **Análisis (Ángel, 3 defectos, 35 min).** (1) `read_csv` con `dtype="category"` tronaba porque la columna `evento` casi siempre venía vacía; se lee como texto y se convierte después, con prueba de regresión. (2) La fórmula `tiempo_s ~ A*B*C + C(bloque)` chocaba con la columna llamada `C` en patsy; se usan dummies explícitas. (3) Al entrar el segundo bloque los residuos dejaron de ser normales (Shapiro p < 0.001) porque los tiempos entre máquinas son multiplicativos; se agregó el modelo `log(tiempo_s)` (R² sube de 0.35 a 0.73) y las conclusiones se mantienen.
- **Datos (Julio, 2 defectos, 35 min).** (1) El extractor trataba el `robots.txt` de APIs públicas como prohibición y J1 fallaba; se rigen por términos de uso con prueba de regresión. (2) Las coordenadas de la tienda piloto solo se podían fijar con variable de entorno y no quedaban confirmadas en CI; se agregaron `TIENDA_LAT`/`TIENDA_LON` en `config.py`.
- **Calidad (José Rey, 5 defectos de revisión).** Dos de documentación sobre normas: `antecedentes-normativos.md` declaraba ISO 9001:2015 como vigente (es la 9001:2026) y confundía 25019 con 25022; se corrigieron con fuentes. Tres técnicos en `medir_iso25012.py`: línea de 101 caracteres (ruff E501), regex con grupos de captura que generaba `UserWarning` en pandas, y comparación celda a celda que contaba 712 diferencias por los NA de pandas 3 (se compara el texto crudo del CSV, 68 celdas, igual que `diff`).

Pendientes conocidos (sin corregir todavía, para E3): coordenadas reales de El Amiguito confirmadas y visita al dueño (J7), captura de ventas reales (hoy todo es `pos_demo`, semilla 42), gitleaks en CI, y la auditoría cruzada R4 (al cierre no se había asignado el equipo auditado).

## 5. ¿Qué aprendimos de cada materia?

- **Ingeniería de Datos (Julio).** Que una capa medallón vale lo que su linaje: `pipeline/linaje.py` toma una fila de oro, abre su `.meta.json` en bronce y **vuelve a calcular el SHA-256**; si alguien altera el crudo, el verificador lo detecta. También que `robots.txt` no reemplaza los términos de uso: Overpass y Open-Meteo son APIs públicas con términos propios y el extractor los distingue con `APIS_CON_TERMINOS`.
- **Análisis Estadístico (Ángel).** Que la configuración actual del pipeline (1 proceso, texto, CSV) tarda **0.253 s** y la óptima (**1 proceso, texto, Parquet**) tarda **0.048 s**: **81.2 % más rápido**, confirmado con 5 corridas nuevas por lado (t de Welch, p = 8.6 × 10⁻⁸). También, que **A (procesos) y C (formato) son significativos** (p = 3.2 × 10⁻⁷ y 6.7 × 10⁻⁴ en el modelo con bloque y log); y que **4 procesos lo hacen más lento** (×3.5) porque arrancar procesos e intercambiar datos cuesta más de lo que se ahorra con archivos de este tamaño (137 867 tickets).
- **Calidad (José Rey).** Que una evaluación de ISO/IEC 25010 sirve cuando cada calificación sale de una medición, no de una opinión: el cumplimiento se midió con `ruff`, `pytest`, `radon`, `pip-audit` y la propia `confirmacion.csv` del experimento (eficiencia 82.1 %, compatibilidad 2/2 formatos, 0 vulnerabilidades). Y que el mayor hueco del producto hoy es la **capacidad de interacción**: 0 de 5 tareas probadas con un usuario real, porque la visita a la tienda (J7) aún está pendiente.

## 6. Evidencias

- Repositorio del E2: https://github.com/salvadorafer11/abarrotespos — etiqueta `e2`.
- **Análisis:** `laboratorio/experimento_E2.ipynb` (cuaderno que corre de principio a fin), `laboratorio/resultados/` (ANOVA, efectos, confirmación, gráficas de interacción y residuos).
- **Datos:** `data/bronce/open_meteo/2026-11/` y `data/bronce/osm_overpass/2026-11/` (capturas con SHA-256 y licencia), `pipeline/geo.py`, `pipeline/linaje.py`, `docs/linaje.md`.
- **Calidad:** `calidad/mediciones/iso25010.json`, `iso25012.json`, `ruff.txt`, `pytest.txt`, `radon-cc.txt`, `radon-mi.txt`, `pip-audit-*.txt`, `pipeline-tiempos.txt`; documentos `docs/calidad/iso25010.md`, `iso25012.md`, `antecedentes-normativos.md`, `docs/plan-sqa.md`.
- Bitácoras: `calidad/tiempo-*.csv`, `calidad/defectos-*.csv`.

**Uso de IA.** Claude (Anthropic) se usó para el esqueleto del repositorio, el extractor y los scripts del pipeline, el script del experimento, el cuaderno, los scripts de medición ISO y la redacción de documentos. Julio y Ángel trabajaron con Claude Code; José Rey con Claude Code; todos revisaron la salida. Las decisiones de diseño (cambio de tema, ruta del experimento, factores, metas de calidad, qué defectos registrar) las tomó el equipo. Cada integración de rama se validó con `ruff check .` y `pytest -q` (11 pruebas en verde).
