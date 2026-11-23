# E2 · Experimento y auditoría — ficha de entrega

Entrega: lunes 23 de noviembre de 2026 · Etiqueta: `e2` · Repositorio nuevo por cambio de tema ([por qué](pivote-abarrotespos.md)).

Estado al iniciar el día (05:40): esqueleto del repositorio con pipeline bronce → plata → oro funcionando sobre ventas de demostración, extractores de clima y OpenStreetMap, experimento factorial programado, CI y pruebas en verde. Lo demás se marca abajo conforme se termina.

| Materia | Criterio (pts) | Responsable | Evidencia | Estado |
|---|---|---|---|---|
| Ing. Datos | Fuente especializada integrada y en tablero (45) | Julio | `extractores/tiendas_osm.py`, mapa en `tablero/app.py` | Extractor y mapa listos; falta primera captura y GeoPandas |
| Ing. Datos | Ética y legalidad por fuente (30) | Julio | `docs/etica-datos.md` | Borrador |
| Ing. Datos | Linaje (15) | Julio | columnas `fuente`, `archivo_bronce`, `capturado_utc` en oro + `docs/linaje.md` | Columnas listas; falta documento |
| Estadística | 2³ con aleatorización, réplicas, bloqueo (25) | Ángel | `laboratorio/resultados/corridas_2k3.csv` | Script listo; faltan corridas reales |
| Estadística | Dos factores con interacción (20) | Ángel | `corridas_dos_factores.csv`, `anova_dos_factores.csv` | Pendiente |
| Estadística | Completo vs fraccionado (20) | Ángel | `matriz_2k4_completa.csv`, `matriz_2k4-1_fraccionada.csv`, `alias_2k4-1.csv` | Matrices generadas; falta explicación |
| Estadística | Análisis y confirmación (25) | Ángel | `anova_2k3.csv`, `interacciones.png`, `residuos.png`, `confirmacion.csv` | Pendiente |
| Calidad | ISO/IEC 25010 (30) | José Rey | `docs/calidad/iso25010.md` | Métricas definidas; faltan mediciones |
| Calidad | ISO/IEC 25012 (25) | José Rey | `docs/calidad/iso25012.md` | Métricas definidas; faltan mediciones |
| Calidad | Antecedentes normativos (10) | José Rey | `docs/calidad/antecedentes-normativos.md` | Plantilla |
| Calidad | Auditoría cruzada (25) | José Rey | `docs/calidad/auditoria-cruzada.md` | Plantilla |
| Las tres | Relatoría (10 c/u) | Ángel | `docs/relatoria-E2.md` | Plantilla |
