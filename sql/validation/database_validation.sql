SELECT
    'raw.ppr_transactions' AS table_name,
    count(*) AS row_count
FROM raw.ppr_transactions
UNION ALL
SELECT
    'staging.ppr_transactions' AS table_name,
    count(*) AS row_count
FROM staging.ppr_transactions
UNION ALL
SELECT
    'raw.rppi_series' AS table_name,
    count(*) AS row_count
FROM raw.rppi_series
UNION ALL
SELECT
    'staging.rppi_series' AS table_name,
    count(*) AS row_count
FROM staging.rppi_series
UNION ALL
SELECT
    'raw.planning_applications' AS table_name,
    count(*) AS row_count
FROM raw.planning_applications
UNION ALL
SELECT
    'staging.planning_applications' AS table_name,
    count(*) AS row_count
FROM staging.planning_applications
UNION ALL
SELECT
    'analytics.monthly_market' AS table_name,
    count(*) AS row_count
FROM analytics.monthly_market
UNION ALL
SELECT
    'analytics.county_market' AS table_name,
    count(*) AS row_count
FROM analytics.county_market
UNION ALL
SELECT
    'analytics.planning_activity' AS table_name,
    count(*) AS row_count
FROM analytics.planning_activity;

SELECT
    min(sale_date) AS ppr_start_date,
    max(sale_date) AS ppr_end_date,
    count(*) AS transactions,
    sum(price_eur)::numeric(18, 2) AS total_value
FROM staging.ppr_transactions;

SELECT
    year_month,
    transactions,
    median_price,
    national_rppi
FROM analytics.monthly_market
ORDER BY year_month DESC
LIMIT 12;

SELECT
    county,
    sale_year,
    transactions,
    median_price
FROM analytics.county_market
ORDER BY sale_year DESC, transactions DESC
LIMIT 20;

SELECT
    planning_authority,
    year_month,
    applications,
    granted_applications,
    residential_units
FROM analytics.planning_activity
ORDER BY year_month DESC, applications DESC
LIMIT 20;

