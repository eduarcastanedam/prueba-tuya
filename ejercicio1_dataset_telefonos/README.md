# Ejercicio 1 — Dataset de números de teléfono de clientes (conceptual)

## Objetivo

Producir y mantener, de forma automatizada, una tabla `telefonos_clientes`
confiable (deduplicada, validada, con procedencia) que otras áreas puedan
consumir con confianza para contactar clientes.

## Fuentes

Múltiples sistemas origen suelen aportar teléfonos (CRM, banca móvil, call
center, formularios web, cobranza). Cada fuente entra como su propia tabla
"raw", sin transformar — la trazabilidad empieza ahí.

## Pipeline (alto nivel)

```
[Fuentes raw] --(extract)--> [staging] --(validar+normalizar)--> [candidatos]
                                                    |
                                          (reglas de resolución)
                                                    v
                                      [telefonos_clientes] (dataset confiable)
```

1. **Extract**: jobs programados por fuente, append-only a `staging.<fuente>`
   con metadata técnica (`fuente`, `cargado_en`, `id_lote`).
2. **Normalizar**: formato E.164, remover caracteres no numéricos, inferir y
   validar indicativo de país, marcar longitud inválida.
3. **Validar**: reglas de negocio — teléfono no nulo/vacío, no es un valor
   centinela ("0000000000"), coincide con patrón de celular/fijo esperado.
   Los que no pasan quedan en `rechazados` con el motivo, no se descartan
   silenciosamente.
4. **Resolver duplicados/conflictos**: un mismo cliente puede tener el mismo
   número repetido en varias fuentes, o números distintos entre fuentes. Se
   aplica una jerarquía de confianza por fuente (ej. verificado por OTP >
   CRM actualizado > formulario web) y se conserva score + histórico de
   cambios (SCD tipo 2) en vez de sobrescribir sin dejar rastro.
5. **Publicar**: solo pasa a `telefonos_clientes` (la tabla que consumen los
   equipos de negocio) lo que superó validación y resolución. Nunca se
   escribe directo ahí desde extract.

## CI/CD

- **Repo** con: definiciones de esquema (DDL versionado), reglas de
  validación como código (tests unitarios sobre la función de
  normalización/validación), y la definición del pipeline (ej. Airflow DAG /
  dbt models).
- **CI** en cada PR: lint + tests unitarios de las reglas de validación
  (casos borde: número con extensión, con espacios, internacional, vacío,
  centinela) + un test de esquema contra una muestra de datos fixture.
- **CD**: al hacer merge a main, deploy automático del DAG/modelos al
  orquestador de un ambiente de staging; promoción a producción requiere
  aprobación manual (gate) y corre contra una copia de datos de prueba antes
  de tocar la tabla real.
- **Mantenimiento**: el job corre en un schedule (ej. diario); si una corrida
  falla o el % de rechazados de un lote se dispara por encima de un umbral,
  se alerta y el lote no se promueve automáticamente (evita contaminar el
  dataset confiable con un problema de fuente upstream).
