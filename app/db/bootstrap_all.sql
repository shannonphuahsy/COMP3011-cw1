------------------------------------------------------------
-- SCHEMAS
------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS api;

------------------------------------------------------------
-- WIFI HOTSPOT TABLE
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.core_wifi_hotspot (
  wifi_id              text PRIMARY KEY,
  name                 text,
  address              text,
  postcode             text,
  city                 text,
  latitude             double precision,
  longitude            double precision,
  status               text,
  venue_type           text,
  network_provider     text,
  security_protection  text,
  accessibility_policy text,
  govroam_enabled      boolean,
  date_live            date,
  easting              double precision,
  northing             double precision,
  wkt_point            text,
  coverage_radius_m    double precision,
  coverage_polygon_wkt text,
  url                  text,
  description          text,
  uprn                 text,
  install_type         text,
  source_dataset       text,
  source_row_id        text,
  geom_geog            geography(Point, 4326),
  geom_geom            geometry(Point, 4326)
);

------------------------------------------------------------
-- CRIME TABLE
------------------------------------------------------------
CREATE TABLE core.core_crime (
  id            bigserial PRIMARY KEY,
  crime_id      text,
  month         text,     -- ← import as text
  reported_by   text,
  falls_within  text,
  longitude     double precision,
  latitude      double precision,
  location      text,
  lsoa_code     text,
  lsoa_name     text,
  crime_type    text,
  outcome       text,
  month_date    text,     -- ← import as text
  geom_geog     geography(Point, 4326)
);

ALTER TABLE core.core_crime
ADD COLUMN crime_date date;

UPDATE core.core_crime
SET crime_date =
    CASE
        WHEN month ~ '^[0-9]{4}-[0-9]{2}$' THEN TO_DATE(month, 'YYYY-MM')
        WHEN month ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN TO_DATE(month, 'YYYY-MM-DD')
        WHEN month_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' THEN CAST(month_date AS date)
        ELSE NULL
    END;

CREATE INDEX idx_crime_crimedate ON core.core_crime (crime_date);
------------------------------------------------------------
-- POSTCODE DIRECTORY
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.core_postcode (
  postcode7 text,
  postcode8 text,
  postcode_egif text,
  date_introduced date,
  date_terminated date,
  user_type text,
  easting double precision,
  northing double precision,
  lat double precision,
  lon double precision,
  positional_quality text,
  lad_2025 text,
  ward_2025 text,
  parish_2025 text,
  oa_2021 text,
  lsoa_2021 text,
  msoa_2021 text,
  nhs_region_2024 text,
  icb_2023 text,
  sub_icb_2024 text,
  cancer_alliance_2024 text,
  police_2023 text,
  imd_2020 text,
  ttwa_2015 text,
  itl_2025 text,
  bua_2024 text,
  lep2021_1 text,
  lep2021_2 text
);

------------------------------------------------------------
-- LSOA GEOMETRY
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.core_lsoa21_geom (
  lsoa21cd       text PRIMARY KEY,
  lsoa21nm       text,
  la_name        text,
  lsoa_local_label text,
  lat            double precision,
  long           double precision,
  bng_e          double precision,
  bng_n          double precision,
  shape__area    double precision,
  shape__length  double precision,
  area_km2       double precision,
  geom_geom      geometry(Point, 4326)
);

------------------------------------------------------------
-- LSOA POPULATION
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.core_lsoa21_population (
  lad21cd    text,
  lad21nm    text,
  lsoa21cd   text PRIMARY KEY,
  lsoa21nm   text,
  total      integer,
  pop_0_15   integer,
  pop_16_24  integer,
  pop_25_64  integer,
  pop_65_plus integer
);

------------------------------------------------------------
-- OPTIONAL: LSOA CONTEXT
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.core_lsoa21_context (
  lsoa21cd    text PRIMARY KEY,
  lsoa21nm    text,
  lad21cd     text,
  lad21nm     text,
  area_km2    double precision,
  total       integer,
  pop_0_15    integer,
  pop_16_24   integer,
  pop_25_64   integer,
  pop_65_plus integer,
  device_density_per_km2 double precision
);

------------------------------------------------------------
-- SPATIAL INDEXES (created after loading data)
------------------------------------------------------------
-- These will be run later after CSV import

------------------------------------------------------------
-- UPDATE GEOMETRY COLUMNS NOW THAT DATA EXISTS
------------------------------------------------------------
UPDATE core.core_wifi_hotspot
SET geom_geog = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
    geom_geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE longitude IS NOT NULL AND latitude IS NOT NULL;

UPDATE core.core_crime
SET geom_geog = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE longitude IS NOT NULL AND latitude IS NOT NULL;

UPDATE core.core_lsoa21_geom
SET geom_geom = ST_SetSRID(ST_MakePoint(long, lat), 4326)
WHERE long IS NOT NULL AND lat IS NOT NULL;

------------------------------------------------------------
-- SPATIAL INDEXES
------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_wifi_geog_gist   ON core.core_wifi_hotspot USING gist (geom_geog);
CREATE INDEX IF NOT EXISTS idx_crime_geog_gist  ON core.core_crime        USING gist (geom_geog);
CREATE INDEX IF NOT EXISTS idx_lsoa_geom_point  ON core.core_lsoa21_geom  USING gist (geom_geom);

------------------------------------------------------------
-- ATTRIBUTE INDEXES
------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_crime_month   ON core.core_crime (month);
CREATE INDEX IF NOT EXISTS idx_postcode7     ON core.core_postcode (postcode7);
CREATE INDEX IF NOT EXISTS idx_postcode_lsoa ON core.core_postcode (lsoa_2021);

------------------------------------------------------------
-- CREATE API VIEWS
------------------------------------------------------------

CREATE OR REPLACE VIEW api.api_wifi_hotspot_enriched AS
SELECT
  w.*,
  p.lsoa_2021 AS lsoa21cd
FROM core.core_wifi_hotspot w
LEFT JOIN core.core_postcode p
  ON upper(replace(w.postcode,' ','')) = upper(replace(p.postcode7,' ',''))

  OR upper(replace(w.postcode,' ','')) = upper(replace(p.postcode8,' ',''));

CREATE OR REPLACE VIEW api.api_wifi_hotspot_with_context AS
SELECT
  h.*,
  c.total AS lsoa_total_pop,
  c.area_km2,
  c.device_density_per_km2
FROM api.api_wifi_hotspot_enriched h
LEFT JOIN core.core_lsoa21_context c
  ON c.lsoa21cd = h.lsoa21cd;

------------------------------------------------------------
-- MATERIALIZED VIEW: CRIME IN LAST 12 MONTHS WITHIN 500 M
------------------------------------------------------------

CREATE MATERIALIZED VIEW api.api_hotspot_crime_12m_500m AS
SELECT
  h.wifi_id,
  COUNT(*)::int AS crime_12m_count
FROM api.api_wifi_hotspot_with_context h
JOIN core.core_crime c
  ON c.crime_date >= (CURRENT_DATE - INTERVAL '12 months')
 AND ST_DWithin(h.geom_geog, c.geom_geog, 500)
GROUP BY h.wifi_id;


CREATE INDEX IF NOT EXISTS idx_mv_hotspot_crime_wifi
  ON api.api_hotspot_crime_12m_500m (wifi_id);

-- Populate it now
REFRESH MATERIALIZED VIEW api.api_hotspot_crime_12m_500m;

------------------------------------------------------------
-- FINAL API VIEW (RISK SCORE)
------------------------------------------------------------
CREATE OR REPLACE VIEW api.api_wifi_hotspot_risk AS
SELECT
  h.*,
  m.crime_12m_count,
  ROUND((
      COALESCE( LN(1 + device_density_per_km2), 0) * 0.5
    + CASE LOWER(COALESCE(h.security_protection, ''))
        WHEN 'open' THEN 2.0
        WHEN 'wpa2' THEN 0.5
        ELSE 1.0
      END
    + COALESCE(m.crime_12m_count / 10.0, 0)
  )::numeric, 2) AS cyber_exposure_score
FROM api.api_wifi_hotspot_with_context h
LEFT JOIN api.api_hotspot_crime_12m_500m m
  ON m.wifi_id = h.wifi_id;

-- 1. Mapping table for BSSID → WiFi Hotspot
CREATE TABLE IF NOT EXISTS api.api_wifi_bssid_map (
    bssid TEXT PRIMARY KEY,
    wifi_id TEXT REFERENCES core.core_wifi_hotspot(wifi_id)
);

-- 2. User incidents (CRUD model)
CREATE TABLE IF NOT EXISTS api.api_user_incidents (
    id SERIAL PRIMARY KEY,
    wifi_id TEXT REFERENCES core.core_wifi_hotspot(wifi_id),
    bssid TEXT,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Recommended indexes
CREATE INDEX IF NOT EXISTS idx_bssid_wifi ON api.api_wifi_bssid_map (wifi_id);
CREATE INDEX IF NOT EXISTS idx_incidents_wifi ON api.api_user_incidents (wifi_id);