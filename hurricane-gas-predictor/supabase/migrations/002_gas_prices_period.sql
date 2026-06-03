-- Add period + series columns to gas_prices for proper dedup and time-series ordering
ALTER TABLE gas_prices ADD COLUMN IF NOT EXISTS period date;
ALTER TABLE gas_prices ADD COLUMN IF NOT EXISTS series text;

-- Unique constraint prevents duplicate inserts across ETL runs
CREATE UNIQUE INDEX IF NOT EXISTS gas_prices_series_period_idx
    ON gas_prices(series, period)
    WHERE period IS NOT NULL;

-- Index for period-based range queries used by the API
CREATE INDEX IF NOT EXISTS gas_prices_period_idx ON gas_prices(period DESC);
