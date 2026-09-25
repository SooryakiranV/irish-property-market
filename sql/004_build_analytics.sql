TRUNCATE TABLE
    analytics.monthly_market,
    analytics.county_market,
    analytics.planning_activity,
    analytics.property_market_summary;

INSERT INTO analytics.monthly_market (
    year_month,
    month_start,
    transactions,
    total_value,
    mean_price,
    median_price,
    national_rppi
)
WITH ppr_monthly AS (
    SELECT
        sale_year_month AS year_month,
        date_trunc('month', sale_date)::date AS month_start,
        count(*)::integer AS transactions,
        sum(price_eur)::numeric(18, 2) AS total_value,
        avg(price_eur)::numeric(14, 2) AS mean_price,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY price_eur)::numeric(14, 2) AS median_price
    FROM staging.ppr_transactions
    GROUP BY sale_year_month, date_trunc('month', sale_date)::date
),
national_rppi AS (
    SELECT
        year_month,
        rppi_value AS national_rppi
    FROM staging.rppi_series
    WHERE property_series = 'National - all residential properties'
      AND unit = 'Base 2015=100'
)
SELECT
    ppr_monthly.year_month,
    ppr_monthly.month_start,
    ppr_monthly.transactions,
    ppr_monthly.total_value,
    ppr_monthly.mean_price,
    ppr_monthly.median_price,
    national_rppi.national_rppi
FROM ppr_monthly
LEFT JOIN national_rppi
    ON ppr_monthly.year_month = national_rppi.year_month
ORDER BY ppr_monthly.year_month;

INSERT INTO analytics.county_market (
    county,
    sale_year,
    transactions,
    total_value,
    mean_price,
    median_price,
    new_property_transactions,
    second_hand_property_transactions
)
SELECT
    county,
    sale_year,
    count(*)::integer AS transactions,
    sum(price_eur)::numeric(18, 2) AS total_value,
    avg(price_eur)::numeric(14, 2) AS mean_price,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY price_eur)::numeric(14, 2) AS median_price,
    count(*) FILTER (WHERE is_new_property)::integer AS new_property_transactions,
    count(*) FILTER (WHERE is_second_hand_property)::integer AS second_hand_property_transactions
FROM staging.ppr_transactions
GROUP BY county, sale_year
ORDER BY county, sale_year;

INSERT INTO analytics.planning_activity (
    planning_authority,
    year_month,
    month_start,
    applications,
    granted_applications,
    refused_applications,
    residential_units
)
SELECT
    planning_authority,
    to_char(date_trunc('month', received_date), 'YYYY-MM') AS year_month,
    date_trunc('month', received_date)::date AS month_start,
    count(*)::integer AS applications,
    count(*) FILTER (WHERE decision ILIKE '%grant%' OR decision ILIKE '%conditional%')::integer AS granted_applications,
    count(*) FILTER (WHERE decision ILIKE '%refus%')::integer AS refused_applications,
    sum(num_residential_units)::numeric(14, 2) AS residential_units
FROM staging.planning_applications
WHERE received_date IS NOT NULL
GROUP BY
    planning_authority,
    to_char(date_trunc('month', received_date), 'YYYY-MM'),
    date_trunc('month', received_date)::date
ORDER BY planning_authority, year_month;

INSERT INTO analytics.property_market_summary (
    metric_name,
    metric_value,
    metric_text
)
SELECT 'ppr_transactions', count(*)::numeric(18, 2), NULL
FROM staging.ppr_transactions
UNION ALL
SELECT 'ppr_total_value_eur', sum(price_eur)::numeric(18, 2), NULL
FROM staging.ppr_transactions
UNION ALL
SELECT 'ppr_start_date', NULL, min(sale_date)::text
FROM staging.ppr_transactions
UNION ALL
SELECT 'ppr_end_date', NULL, max(sale_date)::text
FROM staging.ppr_transactions
UNION ALL
SELECT 'rppi_rows', count(*)::numeric(18, 2), NULL
FROM staging.rppi_series
UNION ALL
SELECT 'planning_applications', count(*)::numeric(18, 2), NULL
FROM staging.planning_applications;

