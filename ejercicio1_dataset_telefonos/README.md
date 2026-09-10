# Ejercicio 1 — Dataset de números de teléfono de clientes

Implementación real (no solo conceptual) con el stack que uso en el día a
día: **Python + PostgreSQL + GitHub Actions + Docker Compose**.

## Cómo correrlo localmente

```bash
docker compose up -d                 # Postgres local en localhost:5433
python -m venv .venv && .venv\Scripts\Activate.ps1   # Windows
python -m pip install -r requirements.txt

pytest tests/ -v                     # reglas de validación
python -m pipeline.cargar --csv data/fuente_ejemplo.csv --fuente crm --id-lote lote-001
```

`pipeline/cargar.py` aplica `schema.sql` si hace falta, carga el CSV a
`staging_telefonos`, valida cada registro y publica en `telefonos_clientes`
(o `rechazados`, con el motivo). Con `data/fuente_ejemplo.csv` (7 filas: 4
válidas, 3 inválidas por distintos motivos) el resultado esperado es:

```
Lote lote-001: 7 filas en staging -> 4 publicadas, 3 rechazadas.
```

## Pipeline

```
[Fuente(s), ej. CRM/call center] --extract (CSV/DB)--> staging_telefonos
                                                              |
                                              pipeline/normalizar.py (reglas)
                                                    /                  \
                                          válido                   inválido
                                             v                          v
                                  telefonos_clientes            rechazados
                                  (histórico SCD2)              (con motivo)
```

- **`pipeline/normalizar.py`**: reglas de negocio puras (sin I/O), fáciles de
  testear. Limpia formato, asume indicativo Colombia (+57) si no viene, y
  rechaza vacíos, valores centinela (`0000000000`) y longitudes inválidas —
  desde el plan de numeración unificado de la CRC (2021) tanto celular como
  fijo con indicativo de área usan 10 dígitos locales.
- **`pipeline/cargar.py`**: orquesta extract → staging → validar → publicar,
  con historial tipo SCD 2 en `telefonos_clientes` (un cambio de número
  cierra la fila anterior con `vigente_hasta` en vez de sobrescribirla).
- **`schema.sql`**: `staging_telefonos`, `rechazados`, `telefonos_clientes`.

## CI/CD (`.github/workflows/ejercicio1-dataset-telefonos.yml`)

Se dispara solo cuando cambia algo dentro de esta carpeta:

1. **`test`** (en cada PR y push a `main`): instala dependencias y corre
   `pytest` sobre las reglas de validación.
2. **`build-and-load`** (solo en `main`, después de que `test` pasa): levanta
   un Postgres efímero como *service container* y corre el pipeline completo
   (`pipeline.cargar`) de punta a punta contra `data/fuente_ejemplo.csv` —
   verifica que lo que se mergea realmente funciona end-to-end antes de
   asumir que serviría para promoverse a un ambiente real. En producción,
   este job apuntaría con `DATABASE_URL` (secret de GitHub Actions) a la
   base real y al CSV/extracción de la fuente correspondiente, siguiendo el
   mismo patrón de test→deploy con Docker que ya uso en mis proyectos.

## Supuestos documentados

- Se asume Colombia como país por defecto (`+57`) cuando el dato no trae
  indicativo — ajustable vía el parámetro `pais_default` de
  `normalizar_telefono`.
- `data/fuente_ejemplo.csv` simula una única fuente (`crm`); con múltiples
  fuentes reales, `staging_telefonos.fuente` ya queda listo para aplicar una
  jerarquía de confianza entre ellas antes de publicar (no implementada aquí
  por no tener una segunda fuente con la que probarla).
