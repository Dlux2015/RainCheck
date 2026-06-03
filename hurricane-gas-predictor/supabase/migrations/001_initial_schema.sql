-- RainCheck initial schema
-- Run this in the Supabase SQL editor for your project

-- Active storms (current snapshot, upserted on each ETL run)
create table if not exists storms (
    storm_id    text primary key,
    storm_name  text,
    status      text,
    lat         double precision,
    lon         double precision,
    wind_speed_kt integer,
    active      boolean not null default true,
    recorded_at timestamptz not null default now()
);

-- Full track history (one row per advisory per storm)
create table if not exists storm_track (
    id            uuid primary key default gen_random_uuid(),
    storm_id      text not null references storms(storm_id),
    lat           double precision,
    lon           double precision,
    wind_speed_kt integer,
    recorded_at   timestamptz not null default now()
);
create index if not exists storm_track_storm_id_idx on storm_track(storm_id);
create index if not exists storm_track_recorded_at_idx on storm_track(recorded_at);

-- Boolean flag: is any storm currently active? (read by price-poll workflow)
create table if not exists storm_flags (
    id         uuid primary key default gen_random_uuid(),
    active     boolean not null,
    created_at timestamptz not null default now()
);

-- Gulf Coast gas prices (appended by price-poll GitHub Action)
create table if not exists gas_prices (
    id          uuid primary key default gen_random_uuid(),
    region      text not null,
    grade       text not null,
    price_usd   double precision not null,
    ingested_at timestamptz not null default now()
);
create index if not exists gas_prices_region_grade_idx on gas_prices(region, grade);
create index if not exists gas_prices_ingested_at_idx on gas_prices(ingested_at);

-- ML buy/wait signals (written by signal writer job, read by /signal/latest)
create table if not exists signals (
    id          uuid primary key default gen_random_uuid(),
    signal      text not null check (signal in ('BUY', 'WAIT')),
    probability double precision not null,
    threshold   double precision not null,
    features    jsonb,
    created_at  timestamptz not null default now()
);
create index if not exists signals_created_at_idx on signals(created_at desc);
