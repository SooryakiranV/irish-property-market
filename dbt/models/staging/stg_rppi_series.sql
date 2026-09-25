{{ config(
    alias='rppi_series',
    post_hook=[
        "create index if not exists idx_staging_rppi_year_month on {{ this }} (year_month)",
        "create index if not exists idx_staging_rppi_property_series on {{ this }} (property_series)"
    ]
) }}

select
    row_number() over (
        order by
            nullif(month, '')::date,
            nullif(property_series, ''),
            nullif("Statistic Label", ''),
            nullif("Type of Residential Property", '')
    )::bigint as rppi_id,
    nullif("Statistic Label", '') as statistic_label,
    nullif("Month", '') as source_month_label,
    nullif("Type of Residential Property", '') as residential_property_type,
    nullif("UNIT", '') as unit,
    nullif("VALUE", '') as source_value,
    nullif(month, '')::date as month_start,
    nullif(year, '')::integer as year,
    nullif(month_number, '')::integer as month_number,
    nullif(quarter, '')::integer as quarter,
    nullif(year_month, '')::char(7) as year_month,
    nullif(property_series, '') as property_series,
    nullif(rppi_value, '')::numeric(10, 2) as rppi_value
from {{ source('raw', 'rppi_series') }}
