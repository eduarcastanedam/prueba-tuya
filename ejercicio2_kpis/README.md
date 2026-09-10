# Ejercicio 2 — Veeduría de calidad y trazabilidad (conceptual)

Construido sobre el resultado real del [ejercicio 1](../ejercicio1_dataset_telefonos/README.md)
(`staging_telefonos`, `rechazados`, `telefonos_clientes`).

## Idea central

Cada corrida de `pipeline/cargar.py` (identificada por `id_lote`) ya deja
rastro suficiente para calcular KPIs directamente con SQL sobre esas tres
tablas, sin necesidad de una tabla de métricas aparte:

- `rechazados` trae el motivo de cada fila descartada, agrupable por lote y
  por fuente.
- `telefonos_clientes` con SCD2 (`vigente_desde`/`vigente_hasta`) permite
  medir frescura y ver el histórico completo de cambios de un cliente.
- `staging_telefonos` vs. `telefonos_clientes` da la tasa de éxito real de
  cada lote.

Para un pipeline con más fuentes, se agregaría una tabla liviana
`metricas_calidad(id_lote, etapa, metrica, valor, fecha_corte)` donde cada
etapa del pipeline escribe su resultado al terminar, evitando recalcular
sobre el dataset completo cada vez que se abre el dashboard.

## KPIs propuestos

- **Completitud**: `% de identificaciones con fila vigente en telefonos_clientes`.
- **Tasa de rechazo por lote/fuente/motivo**:
  ```sql
  SELECT id_lote, fuente, motivo, count(*) 
  FROM rechazados GROUP BY 1,2,3 ORDER BY 1 DESC;
  ```
  Una tendencia al alza en un motivo específico (ej. "longitud inválida")
  para una fuente puntual indica que esa fuente cambió su formato de export.
- **Frescura**: `now() - vigente_desde` por cliente; % de clientes con
  teléfono de más de N meses sin actualizarse.
- **Cambios de teléfono por cliente**: `count(*) por identificacion` en
  `telefonos_clientes` — un número anormalmente alto puede indicar fraude o
  un problema de resolución de duplicados en la fuente.
- **Éxito por lote**: `filas publicadas / filas en staging` por `id_lote` —
  ya queda expuesto en el log que imprime `pipeline/cargar.py` y es
  trivialmente consultable en la base.

## Herramienta

Ya usamos **Metabase** y **Apache Superset** como herramientas de BI, así
que el mecanismo natural es un dashboard ahí, apuntando directo a estas
tablas (sin ETL adicional):

- Vista para negocio: completitud y frescura por segmento de cliente.
- Vista para el equipo de datos: rechazos por fuente/motivo/lote, para
  diagnosticar rápido qué fuente está fallando y por qué.
- Como el pipeline corre vía GitHub Actions (ejercicio 1), cada corrida deja
  el dato fresco automáticamente — el dashboard no requiere refresco manual,
  solo la caché normal de Metabase/Superset.
