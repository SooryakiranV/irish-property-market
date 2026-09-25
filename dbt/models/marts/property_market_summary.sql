{{ config(
    post_hook="create unique index if not exists idx_analytics_property_market_summary_metric on {{ this }} (metric_name)"
) }}

select 'ppr_transactions' as metric_name, count(*)::numeric(18, 2) as metric_value, null as metric_text
from {{ ref('stg_ppr_transactions') }}
union all
select 'ppr_total_value_eur', sum(price_eur)::numeric(18, 2), null
from {{ ref('stg_ppr_transactions') }}
union all
select 'ppr_start_date', null, min(sale_date)::text
from {{ ref('stg_ppr_transactions') }}
union all
select 'ppr_end_date', null, max(sale_date)::text
from {{ ref('stg_ppr_transactions') }}
union all
select 'rppi_rows', count(*)::numeric(18, 2), null
from {{ ref('stg_rppi_series') }}
union all
select 'planning_applications', count(*)::numeric(18, 2), null
from {{ ref('stg_planning_applications') }}
