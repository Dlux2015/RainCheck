---
name: build-features
description: Run bronze-to-silver cleaning and gold-layer feature engineering for model training
---

## Build Features

Promotes data through bronze → silver → gold Delta layers via PySpark.

### Steps
1. Run `python -m src.transforms.bronze_to_silver` — cleans and deduplicates records
2. Run `python -m src.transforms.feature_engineering` — builds ML features and binary labels
3. Optionally run `python -m src.transforms.geo_intersection` to tag at-risk refineries
4. Verify gold table row count and label distribution (target: ~10-20% positive class)
5. Run `pytest` before marking complete

### Rules
- Only bronze is append-only; silver and gold may be overwritten on reprocessing
- All PySpark jobs write with `.format("delta")`
- Labels: `price_pct_change > 0.03` → 1 (BUY), else 0 (WAIT)
