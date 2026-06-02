---
name: ingest-gas-prices
description: Poll Zyla API for Gulf Coast gas prices and append to Delta Lake bronze layer
---

## Ingest Gas Prices

Calls the Zyla US Gas Prices API and appends records to the bronze Delta table.

### Steps
1. Verify `ZYLA_API_KEY` is set in `.env`
2. Run: `python -m src.ingestion.gas_price_ingest`
3. Confirm row count in `dbfs:/delta/bronze/gas_prices`
4. Run `pytest tests/` before marking complete

### Rules
- Bronze layer is **append-only**
- `ZYLA_API_KEY` must come from `os.getenv("ZYLA_API_KEY")` — never hardcoded
- Zyla is a commercial API — requires a paid key; do not commit the key
