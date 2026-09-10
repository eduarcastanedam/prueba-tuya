# Ejercicio 3 — Rachas

## Cómo replicar

```bash
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
python load_data.py                                  # crea db/rachas.db desde ../Rachas.xlsx
python run_query.py --fecha-base 2024-12-31 --n 3     # ejemplo de ejecución
```

> Si `pip` no se reconoce como comando en PowerShell, usa `python -m pip install -r requirements.txt` (o `py -m pip ...`).

- `schema.sql`: tablas `historia` y `retiros`.
- `load_data.py`: lee `Rachas.xlsx` (hojas `historia` y `retiros`) y carga SQLite.
- `query_rachas.sql`: consulta parametrizada (`:fecha_base`, `:n`) con toda la lógica de negocio.
- `run_query.py`: ejecuta la consulta anterior y la imprime en consola.

## Modelo de datos

- `historia(identificacion, corte_mes, saldo)`: saldo de cada cliente por corte de mes.
- `retiros(identificacion, fecha_retiro)`: clientes que se retiraron y cuándo.

## Lógica de la consulta

1. **Calendario por cliente**: para cada cliente se construye la serie completa de
   cortes de mes (tomados de los cortes reales presentes en `historia`, no se asume
   periodicidad perfecta) desde su primera aparición hasta `min(fecha_base, fecha_retiro)`.
2. **Imputación N0**: los meses del calendario sin registro real en `historia` se
   tratan como saldo 0 → N0. Los meses posteriores a `fecha_retiro` no generan fila
   en el calendario (no se imputa nada), tal como pide el enunciado.
3. **Niveles**: N0 (`< 300,000`), N1 (`300,000–1,000,000`), N2 (`1,000,000–3,000,000`),
   N3 (`3,000,000–5,000,000`), N4 (`>= 5,000,000`).
4. **Rachas (gaps and islands)**: se agrupan meses consecutivos del mismo nivel por
   cliente usando la diferencia entre dos `ROW_NUMBER()` (uno global por cliente,
   otro por cliente+nivel); esa diferencia es constante mientras la racha no se rompe.
5. **Filtro y desempate**: se descartan rachas con longitud `< n`; por cliente se
   elige la racha más larga y, en caso de empate, la de `fecha_fin` más reciente.

## Calidad de datos (decisiones documentadas)

- **Duplicados en `historia`**: la fuente trae 2 filas con la misma clave
  `(identificacion, corte_mes)` (una es un duplicado exacto, la otra tiene dos
  saldos distintos para el mismo mes). `load_data.py` las colapsa quedándose con
  el **saldo mayor** (criterio conservador para un caso de uso de riesgo/cobranza)
  y lo reporta por consola. Con esto `historia.(identificacion, corte_mes)` queda
  como clave primaria real.
- **Retiro sin historia asociada**: `retiros` incluye un `identificacion` que nunca
  aparece en `historia`. Al no tener saldo alguno, ese cliente no genera ninguna
  racha (queda naturalmente excluido, no requiere manejo especial).
- **Dato real reportado después de `fecha_retiro`**: en la fuente hay casos donde
  un cliente tiene un registro de saldo en un corte posterior a su fecha de retiro.
  Se asumió que, una vez retirado, el cliente queda fuera del análisis
  (esos registros se ignoran), en vez de tratarlos como saldo vigente. El enunciado
  no lo especifica explícitamente; queda documentado como supuesto.
