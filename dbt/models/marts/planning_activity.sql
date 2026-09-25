{{ config(
    post_hook="create index if not exists idx_analytics_planning_activity_authority_month on {{ this }} (planning_authority, year_month)"
) }}

select
    planning_authority,
    to_char(date_trunc('month', received_date), 'YYYY-MM') as year_month,
    date_trunc('month', received_date)::date as month_start,
    count(*)::integer as applications,
    count(*) filter (where decision ilike '%grant%' or decision ilike '%conditional%')::integer as granted_applications,
    count(*) filter (where decision ilike '%refus%')::integer as refused_applications,
    sum(num_residential_units)::numeric(14, 2) as residential_units
from {{ ref('stg_planning_applications') }}
where received_date is not null
group by
    planning_authority,
    to_char(date_trunc('month', received_date), 'YYYY-MM'),
    date_trunc('month', received_date)::date
