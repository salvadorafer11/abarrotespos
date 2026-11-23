# Relatoría E2 · AbarrotesPOS

Máximo dos páginas. Específica (fechas, números, nombres), honesta (lo que salió mal) y verificable (cada afirmación con evidencia).

## 1. ¿Qué nos propusimos?
Cambiar de ObraPrecio a AbarrotesPOS y, en la misma semana, (a) integrar una fuente geoespacial al tablero, (b) encontrar con un 2³ la configuración del pipeline que procesa más rápido las ventas y cuánto mejora, y (c) evaluar el sistema con ISO/IEC 25010 y 25012. PENDIENTE: ajustar con los números finales.

## 2. ¿Qué hicimos? (sale de `calidad/tiempo-*.csv`)
| Fecha | Qué | Quién | Tiempo |
|---|---|---|---|
| 18-nov | Sesión con el profe Mónico: vinculación con pymes, idea de analítica de ventas | Ángel | — |
| 20-nov | Revisión de la lluvia de 20 ideas; el profe marca factibles 10, 15–18 y propone la tienda El Amiguito | Equipo | — |
| 22-nov | Decisión de cambio de tema en el grupo | Equipo | — |
| 23-nov | Repositorio nuevo con pipeline, extractores y experimento | Ángel (con IA) | PENDIENTE |
| 23-nov | PENDIENTE: fuente geoespacial, ética, linaje | Julio | |
| 23-nov | PENDIENTE: ISO 25010/25012, auditoría cruzada | José Rey | |

## 3. ¿Qué decidimos y por qué?
- Cambiar de tema: ObraPrecio necesitaba clientes muy específicos; AbarrotesPOS tiene cliente piloto y mercado en cualquier colonia. Descartado: seguir con ObraPrecio, ideas 15–18 (campañas, aire acondicionado, dark kitchens, sucursales).
- Ruta ingeniería en el experimento, para no depender del cliente esta semana. Descartado: ruta negocio (precio vs. promoción en la tienda), queda para E3.
- Fuente especializada: OpenStreetMap (sin token) con DENUE como respaldo. PENDIENTE confirmar.

## 4. ¿Qué salió mal y cómo lo corregimos? (ligado a `calidad/defectos-*.csv`)
PENDIENTE.

## 5. ¿Qué aprendimos de cada materia?
- **Ingeniería de Datos:** PENDIENTE (Julio).
- **Análisis Estadístico:** PENDIENTE (Ángel).
- **Calidad:** PENDIENTE (José Rey).

## 6. Evidencias
PENDIENTE: enlaces a commits, `laboratorio/resultados/`, capturas del tablero, PRs.

**Uso de IA:** Claude (Anthropic) se usó para armar el esqueleto del repositorio, el extractor de OpenStreetMap, el generador de ventas de demostración y el script del experimento, y para sintetizar las grabaciones de las sesiones con el profe. PENDIENTE: lo que use cada integrante (Codex/ChatGPT, etc.).
