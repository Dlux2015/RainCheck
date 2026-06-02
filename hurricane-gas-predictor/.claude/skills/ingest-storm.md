---
name: ingest-storm
description: Fetch latest NHC Atlantic storm data from RSS and append to Delta Lake bronze layer
---

## Ingest Storm Data

Fetches the NHC RSS feed and appends storm records to the bronze Delta table.

### Steps
1. Verify `NHC_RSS_URL` is set in `.env` (defaults to NHC Atlantic feed)
2. Run: `python -m src.ingestion.storm_ingest`
3. Confirm row count in `dbfs:/delta/bronze/storms`
4. Run `pytest tests/test_storm_ingest.py` before marking complete

### Rules
- Bronze layer is **append-only** — never use `.mode("overwrite")` on bronze paths
- `NHC_RSS_URL` must come from `os.getenv()` — never hardcoded
- On zero items returned the function exits early without writing; this is expected outside hurricane season
