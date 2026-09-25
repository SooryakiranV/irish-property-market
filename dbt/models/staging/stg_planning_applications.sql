{{ config(
    alias='planning_applications',
    post_hook=[
        "create index if not exists idx_staging_planning_received_date on {{ this }} (received_date)",
        "create index if not exists idx_staging_planning_authority on {{ this }} (planning_authority)"
    ]
) }}

select
    row_number() over (
        order by
            nullif("OBJECTID", '')::bigint nulls last,
            nullif("ApplicationNumber", ''),
            nullif("ReceivedDate", '')
    )::bigint as planning_id,
    nullif("OBJECTID", '')::bigint as object_id,
    nullif("PlanningAuthority", '') as planning_authority,
    nullif("ApplicationNumber", '') as application_number,
    nullif("DevelopmentDescription", '') as development_description,
    nullif("DevelopmentAddress", '') as development_address,
    nullif("DevelopmentPostcode", '') as development_postcode,
    nullif("ITMEasting", '')::numeric as itm_easting,
    nullif("ITMNorthing", '')::numeric as itm_northing,
    nullif("ApplicationStatus", '') as application_status,
    nullif("ApplicationType", '') as application_type,
    nullif("Decision", '') as decision,
    nullif("LandUseCode", '') as land_use_code,
    nullif("AreaofSite", '')::numeric as area_of_site,
    nullif("NumResidentialUnits", '')::numeric as num_residential_units,
    nullif("OneOffHouse", '') as one_off_house,
    nullif("FloorArea", '')::numeric as floor_area,
    to_timestamp(nullif("ReceivedDate", '')::numeric / 1000)::date as received_date,
    to_timestamp(nullif("WithdrawnDate", '')::numeric / 1000)::date as withdrawn_date,
    to_timestamp(nullif("DecisionDate", '')::numeric / 1000)::date as decision_date,
    to_timestamp(nullif("DecisionDueDate", '')::numeric / 1000)::date as decision_due_date,
    to_timestamp(nullif("GrantDate", '')::numeric / 1000)::date as grant_date,
    to_timestamp(nullif("ExpiryDate", '')::numeric / 1000)::date as expiry_date,
    nullif("AppealRefNumber", '') as appeal_ref_number,
    nullif("AppealStatus", '') as appeal_status,
    nullif("AppealDecision", '') as appeal_decision,
    to_timestamp(nullif("AppealDecisionDate", '')::numeric / 1000)::date as appeal_decision_date,
    to_timestamp(nullif("AppealSubmittedDate", '')::numeric / 1000)::date as appeal_submitted_date,
    to_timestamp(nullif("FIRequestDate", '')::numeric / 1000)::date as further_information_request_date,
    to_timestamp(nullif("FIRecDate", '')::numeric / 1000)::date as further_information_received_date,
    nullif("LinkAppDetails", '') as link_app_details,
    nullif("OneOffKPI", '') as one_off_kpi,
    to_timestamp(nullif("ETL_DATE", '')::numeric / 1000)::date as etl_date,
    nullif("SiteId", '') as site_id,
    nullif("Shape__Area", '')::numeric as shape_area,
    nullif("Shape__Length", '')::numeric as shape_length
from {{ source('raw', 'planning_applications') }}
