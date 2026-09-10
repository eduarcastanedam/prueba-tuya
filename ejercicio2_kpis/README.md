# Ejercicio 2 — Veeduría de calidad y trazabilidad (conceptual)

Construido sobre el pipeline del [ejercicio 1](../ejercicio1_dataset_telefonos/README.md).

## Idea central

Cada etapa del pipeline (staging → validar → resolver → publicar) escribe
sus propias métricas en una tabla `metricas_calidad(id_lote, etapa, metrica,
valor, fecha_corte)`, además de conservar de cada registro publicado su
`id_lote` y `fuente` de origen (trazabilidad ya vive en el dataset mismo,
gracias al SCD tipo 2 del ejercicio 1). Ese log de métricas es la base de los
KPIs, no hace falta recalcularlos leyendo el dataset completo cada vez.

## KPIs propuestos

- **Completitud**: % de clientes activos con al menos un teléfono válido en
  `telefonos_clientes`.
- **Tasa de rechazo**: % de registros que caen en `rechazados` por lote,
  desglosado por fuente y por motivo (para ver si una fuente específica se
  degrada).
- **Duplicidad**: número de conflictos resueltos por lote (mismo cliente,
  fuentes en desacuerdo) — una tendencia al alza indica que una fuente dejó
  de sincronizar bien.
- **Frescura**: días desde la última actualización de teléfono por cliente;
  % de clientes con dato de más de N meses.
- **Trazabilidad**: % de registros publicados con fuente y timestamp
  identificables (debería ser 100%; si baja, algo se está insertando fuera
  del pipeline).
- **Éxito de corrida**: % de lotes que se ejecutaron sin error / con tasa de
  rechazo dentro del umbral esperado.

## Herramienta

Un dashboard (ej. Metabase/Superset) apuntando directo a `metricas_calidad` +
`telefonos_clientes`, con:

- Vista resumen para negocio: completitud y frescura por segmento de
  cliente, con alertas visuales cuando cruzan el umbral.
- Vista técnica para el equipo de datos: tasa de rechazo y duplicidad por
  fuente/lote, para diagnosticar rápido cuál origen está fallando.
- Cada corrida del pipeline (CI/CD del ejercicio 1) inserta sus métricas al
  finalizar, así el dashboard siempre refleja el último lote sin proceso
  manual.
