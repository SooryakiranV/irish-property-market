{{ config(
    alias='ppr_transactions',
    post_hook=[
        "create index if not exists idx_staging_ppr_sale_date on {{ this }} (sale_date)",
        "create index if not exists idx_staging_ppr_county_year on {{ this }} (county, sale_year)",
        "create index if not exists idx_staging_ppr_year_month on {{ this }} (sale_year_month)"
    ]
) }}

select
    row_number() over (
        order by
            nullif(sale_date, '')::date,
            nullif(address, ''),
            nullif(county, ''),
            nullif(price_eur, '')::numeric(14, 2),
            nullif(sale_year_month, '')
    )::bigint as ppr_id,
    nullif(sale_date, '')::date as sale_date,
    nullif(sale_year, '')::integer as sale_year,
    nullif(sale_month, '')::integer as sale_month,
    nullif(sale_quarter, '')::integer as sale_quarter,
    nullif(sale_year_month, '')::char(7) as sale_year_month,
    nullif(address, '') as address,
    nullif(county, '') as county,
    nullif(eircode, '') as eircode,
    nullif(price_eur, '')::numeric(14, 2) as price_eur,
    nullif(not_full_market_price, '') as not_full_market_price,
    coalesce(nullif(is_not_full_market_price, '')::boolean, false) as is_not_full_market_price,
    nullif(vat_exclusive, '') as vat_exclusive,
    coalesce(nullif(is_vat_exclusive, '')::boolean, false) as is_vat_exclusive,
    nullif(property_description, '') as property_description,
    coalesce(nullif(is_new_property, '')::boolean, false) as is_new_property,
    coalesce(nullif(is_second_hand_property, '')::boolean, false) as is_second_hand_property,
    nullif(property_size_description, '') as property_size_description,
    nullif(property_size_category, '') as property_size_category
from {{ source('raw', 'ppr_transactions') }}
