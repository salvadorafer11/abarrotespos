# Antecedentes normativos: ISO/IEC 9126 → SQuaRE (25000) e ISO 9001

Responsable: José Rey Sánchez Navarro. Fecha de revisión: 23-nov-2026. Fuentes al final.

## 1. De ISO/IEC 9126 e ISO/IEC 14598 a SQuaRE

ISO/IEC 9126 (modelo y métricas de calidad del producto) e ISO/IEC 14598 (proceso de evaluación) eran dos familias separadas. SQuaRE (*Systems and software Quality Requirements and Evaluation*, serie ISO/IEC 25000) las unificó y agregó la calidad de los datos. Ambas familias anteriores están retiradas.

| Norma anterior (retirada) | Qué cubría | La sustituye en SQuaRE | Cambio principal |
|---|---|---|---|
| ISO/IEC 9126-1:2001 Modelo de calidad | 6 características del producto (funcionalidad, fiabilidad, usabilidad, eficiencia, mantenibilidad, portabilidad) y un modelo de calidad en uso (efectividad, productividad, seguridad física, satisfacción) | ISO/IEC 25010:2011, reemplazada por **ISO/IEC 25010:2023** | 2011: 8 características (se agregan *seguridad* y *compatibilidad*; funcionalidad pasa a *adecuación funcional*). 2023: 9 características; *usabilidad* se renombra *capacidad de interacción*, *portabilidad* se renombra *flexibilidad* (con la subcaracterística nueva *escalabilidad*) y se agrega *protección (safety)*. La calidad en uso sale de 25010 y pasa a ISO/IEC 25019 |
| ISO/IEC TR 9126-2:2003 Métricas externas | Medir el producto en ejecución (comportamiento observable) | ISO/IEC 25023:2016 | Unifica métricas externas e internas en "medidas de calidad del sistema y del producto", construidas a partir de elementos de medida (ISO/IEC 25021) |
| ISO/IEC TR 9126-3:2003 Métricas internas | Medir el producto sin ejecutarlo (código, diseño) | ISO/IEC 25023:2016 | Igual que la anterior: deja de haber un documento separado para métricas internas |
| ISO/IEC TR 9126-4:2004 Métricas de calidad en uso | Medir efectividad, productividad, seguridad y satisfacción del usuario | ISO/IEC 25022:2016 (medidas); el **modelo** de calidad en uso está en ISO/IEC 25019:2023 | Separa *modelo* (25019) de *medición* (25022); se agregan libertad de riesgo y cobertura de contexto |
| (no existía) | Calidad de los datos | ISO/IEC 25012:2008 (modelo) e ISO/IEC 25024:2015 (medidas) | Novedad de SQuaRE: 15 características de datos, clasificadas como *inherentes* o *dependientes del sistema* |
| ISO/IEC 14598 (partes 1 a 6, 1998–2001) Evaluación del producto | Proceso de evaluación para desarrolladores, adquirentes y evaluadores, y módulos de evaluación | ISO/IEC 25040 (proceso de evaluación), ISO/IEC 25041 (guía por tipo de evaluador) e ISO/IEC 25045 (módulo de recuperabilidad) | El proceso de evaluación queda en una sola norma alineada con el modelo de calidad y la medición de SQuaRE |

## 2. Divisiones de la familia SQuaRE (ISO/IEC 25000)

| División | Tema | Qué contiene (normas de ejemplo) |
|---|---|---|
| 2500n | Gestión de la calidad | Guía general de SQuaRE y vocabulario (25000), planificación y gestión de la evaluación (25001), panorama y uso de los modelos de calidad (25002) |
| 2501n | Modelo de calidad | Producto (25010), servicios de TI (25011), datos (25012), calidad en uso (25019) |
| 2502n | Medición de la calidad | Marco de medición (25020), elementos de medida (25021), medidas de calidad en uso (25022), del producto (25023), de los datos (25024), de servicios de TI (25025) |
| 2503n | Requisitos de calidad | Cómo especificar requisitos de calidad usando los modelos y las medidas (25030) |
| 2504n | Evaluación de la calidad | Proceso de evaluación (25040), guía para desarrolladores, adquirentes y evaluadores (25041), módulos de evaluación (25045) |
| 25050–25099 | Extensión | Requisitos para producto de software listo para usar (25051) y formatos comunes de la industria para reportes de usabilidad (25060–25066) |

**Cómo se usa en este proyecto:** el modelo viene de la división 2501n (25010 y 25012); las métricas de cada fila en [iso25010.md](iso25010.md) e [iso25012.md](iso25012.md) siguen la lógica de la división 2502n (cada valor sale de un elemento de medida reproducible: un comando o un archivo); la evaluación sigue la división 2504n (definir meta → medir → calificar → reportar evidencia).

## 3. ISO 9001 vigente: ISO 9001:2026

- **Qué es:** requisitos de un *sistema de gestión de la calidad de una organización*. No evalúa un producto de software; evalúa cómo la organización planifica, ejecuta, controla y mejora sus procesos para entregar productos que cumplan los requisitos del cliente.
- **Edición vigente:** ISO 9001:2026 (sexta edición), publicada por ISO el 16 de septiembre de 2026. Reemplaza a ISO 9001:2015 y a su enmienda 1:2024. Las certificaciones 2015 siguen válidas durante un periodo de transición de unos tres años (hasta septiembre de 2029 según organismos de certificación; la fecha exacta la fijan las reglas de acreditación).
- **Qué se conserva:** la estructura de cláusulas (estructura armonizada de las normas de sistemas de gestión), el **enfoque a procesos**, el ciclo **PHVA** (planificar–hacer–verificar–actuar) y el **pensamiento basado en riesgos**.
- **Qué cambia en 2026:** más énfasis en liderazgo, cultura de la calidad y comportamiento ético; separa con más claridad *riesgos* y *oportunidades*; agrega un anexo A que explica la intención y la terminología de los requisitos.
- **Puente con el software:** ISO/IEC/IEEE 90003 es la guía para aplicar ISO 9001 a la adquisición, desarrollo y mantenimiento de software (su edición 2018 está escrita sobre ISO 9001:2015).

### Enfoque a procesos (PHVA) reflejado en AbarrotesPOS

| Etapa PHVA | Proceso del proyecto | Evidencia en el repositorio |
|---|---|---|
| Planificar | Objetivos y métricas de calidad, responsables, riesgos | [docs/plan-sqa.md](../plan-sqa.md) (secciones 3, 5.2 y 14), [docs/E2/TAREAS.md](../E2/TAREAS.md) |
| Hacer | Captura de fuentes con ética, pipeline bronce → plata → oro, desarrollo en ramas | `extractores/`, `pipeline/ejecutar.py`, `.github/workflows/captura.yml` |
| Verificar | Puerta de calidad con cuarentena, CI (ruff, pytest, pipeline, pip-audit, gitleaks), evaluación ISO/IEC 25010 y 25012, auditoría cruzada | `ESQUEMA_VENTAS` en `pipeline/ejecutar.py`, `.github/workflows/ci.yml`, [iso25010.md](iso25010.md), [iso25012.md](iso25012.md), [auditoria-cruzada.md](auditoria-cruzada.md) |
| Actuar | Registro de defectos y acciones correctivas, cambios al plan | `calidad/defectos-<nombre>.csv`, sección 8 y control de cambios del plan SQA |

## 4. Confusiones que se evitan en este proyecto

1. **ISO 9001 no es un modelo de calidad del producto.** Certifica el sistema de gestión de una organización; la calidad del software se evalúa con ISO/IEC 25010 y la de los datos con ISO/IEC 25012.
2. **ISO/IEC 25010 (modelo) no es ISO/IEC 25023 (medidas).** La primera dice *qué* características hay; la segunda, *cómo* medirlas.
3. **La calidad en uso ya no está en 25010:2023.** Su modelo está en ISO/IEC 25019 y sus medidas en ISO/IEC 25022.
4. **En 25010:2023, flexibilidad es el nuevo nombre de portabilidad**, no una característica adicional.
5. **ISO/IEC 9126 y 14598 están retiradas.** Se citan sólo como antecedente.
6. **La edición vigente de ISO 9001 es la de 2026.** La de 2015 sólo sigue válida para certificados durante la transición.

## Fuentes consultadas (23-nov-2026)
- ISO. *ISO 9001:2026 — Quality management systems — Requirements*. https://www.iso.org/standard/9001
- ISO. *ISO 9001:2026: What businesses need to know*. https://www.iso.org/quality-management/iso-9001-2026
- ISO. *ISO/IEC 25010:2023 — Product quality model*. https://www.iso.org/standard/78176.html
- arc42 Quality Model. *ISO 25010 update 2023*. https://quality.arc42.org/articles/iso-25010-update-2023
- DQS. *ISO 9001:2026 Is Here* (transición). https://www.dqsglobal.com/en/explore/blog/iso-9001-2026-transition
- NSF. *ISO 9001:2026 published on September 16, 2026*. https://www.nsf.org/za/en/knowledge-library/iso-90012026-published-on-september-16-2026-what-quality-leaders-need-to-know

Nota: las páginas de iso.org no se pudieron descargar de forma automática (respuesta 403); los datos de publicación se confirmaron con los resúmenes de búsqueda de esas páginas y con organismos de certificación. Antes de la defensa conviene abrir las páginas de ISO en el navegador y comprobarlo.
