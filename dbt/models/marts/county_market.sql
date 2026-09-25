{{ config(
    post_hook="create index if not exists idx_analytics_county_market_county_year on {{ this }} (county, sale_year)"
) }}

select
    county,
    sale_year,
    count(*)::integer as transactions,
    sum(price_eur)::numeric(18, 2) as total_value,
    avg(price_eur)::numeric(14, 2) as mean_price,
    percentile_cont(0.5) within group (order by price_eur)::numeric(14, 2) as median_price,
    count(*) filter (where is_new_property)::integer as new_property_transactions,
    count(*) filter (where is_second_hand_property)::integer as second_hand_property_transactions
from {{ ref('stg_ppr_transactions') }}
group by county, sale_year
