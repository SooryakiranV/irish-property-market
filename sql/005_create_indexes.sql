CREATE INDEX IF NOT EXISTS idx_raw_ppr_sale_year_month
    ON raw.ppr_transactions (sale_year_month);

CREATE INDEX IF NOT EXISTS idx_staging_ppr_sale_date
    ON staging.ppr_transactions (sale_date);

CREATE INDEX IF NOT EXISTS idx_staging_ppr_county_year
    ON staging.ppr_transactions (county, sale_year);

CREATE INDEX IF NOT EXISTS idx_staging_ppr_year_month
    ON staging.ppr_transactions (sale_year_month);

CREATE INDEX IF NOT EXISTS idx_staging_rppi_year_month
    ON staging.rppi_series (year_month);

CREATE INDEX IF NOT EXISTS idx_staging_rppi_property_series
    ON staging.rppi_series (property_series);

CREATE INDEX IF NOT EXISTS idx_staging_planning_received_date
    ON staging.planning_applications (received_date);

CREATE INDEX IF NOT EXISTS idx_staging_planning_authority
    ON staging.planning_applications (planning_authority);

