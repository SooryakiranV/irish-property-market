{{ config(
    post_hook="create unique index if not exists idx_analytics_monthly_market_year_month on {{ this }} (year_month)"
) }}

with ppr_monthly as (
    select
        sale_year_month as year_month,
        date_trunc('month', sale_date)::date as month_start,
        count(*)::integer as transactions,
        sum(price_eur)::numeric(18, 2) as total_value,
        avg(price_eur)::numeric(14, 2) as mean_price,
        percentile_cont(0.5) within group (order by price_eur)::numeric(14, 2) as median_price
    from {{ ref('stg_ppr_transactions') }}
    group by sale_year_month, date_trunc('month', sale_date)::date
),

national_rppi as (
    select
        year_month,
        rppi_value as national_rppi
    from {{ ref('stg_rppi_series') }}
    where property_series = 'National - all residential properties'
      and unit = 'Base 2015=100'
)

select
    ppr_monthly.year_month,
    ppr_monthly.month_start,
    ppr_monthly.transactions,
    ppr_monthly.total_value,
    ppr_monthly.mean_price,
    ppr_monthly.median_price,
    national_rppi.national_rppi
from ppr_monthly
left join national_rppi
    on ppr_monthly.year_month = national_rppi.year_month
