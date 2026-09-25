TRUNCATE TABLE
    staging.ppr_transactions,
    staging.rppi_series,
    staging.planning_applications
RESTART IDENTITY;


-- ============================================================
-- PPR TRANSACTIONS
-- ============================================================

INSERT INTO staging.ppr_transactions (
    sale_date,
    sale_year,
    sale_month,
    sale_quarter,
    sale_year_month,
    address,
    county,
    eircode,
    price_eur,
    not_full_market_price,
    is_not_full_market_price,
    vat_exclusive,
    is_vat_exclusive,
    property_description,
    is_new_property,
    is_second_hand_property,
    property_size_description,
    property_size_category
)
SELECT
    NULLIF(sale_date, '')::date,
    NULLIF(sale_year, '')::integer,
    NULLIF(sale_month, '')::integer,
    NULLIF(sale_quarter, '')::integer,
    NULLIF(sale_year_month, '')::char(7),
    NULLIF(address, ''),
    NULLIF(county, ''),
    NULLIF(eircode, ''),
    NULLIF(price_eur, '')::numeric(14, 2),
    NULLIF(not_full_market_price, ''),
    COALESCE(NULLIF(is_not_full_market_price, '')::boolean, false),
    NULLIF(vat_exclusive, ''),
    COALESCE(NULLIF(is_vat_exclusive, '')::boolean, false),
    NULLIF(property_description, ''),
    COALESCE(NULLIF(is_new_property, '')::boolean, false),
    COALESCE(NULLIF(is_second_hand_property, '')::boolean, false),
    NULLIF(property_size_description, ''),
    NULLIF(property_size_category, '')
FROM raw.ppr_transactions;


-- ============================================================
-- RPPI
-- ============================================================

INSERT INTO staging.rppi_series (
    statistic_label,
    source_month_label,
    residential_property_type,
    unit,
    source_value,
    month_start,
    year,
    month_number,
    quarter,
    year_month,
    property_series,
    rppi_value
)
SELECT
    NULLIF("Statistic Label", ''),
    NULLIF("Month", ''),
    NULLIF("Type of Residential Property", ''),
    NULLIF("UNIT", ''),
    NULLIF("VALUE", ''),
    NULLIF(month, '')::date,
    NULLIF(year, '')::integer,
    NULLIF(month_number, '')::integer,
    NULLIF(quarter, '')::integer,
    NULLIF(year_month, '')::char(7),
    NULLIF(property_series, ''),
    NULLIF(rppi_value, '')::numeric(10, 2)
FROM raw.rppi_series;


-- ============================================================
-- PLANNING APPLICATIONS
-- ============================================================
-- Source numeric fields are loaded as unconstrained NUMERIC
-- to prevent valid source values from overflowing.
-- Range/type validation is handled separately.

INSERT INTO staging.planning_applications (
    object_id,
    planning_authority,
    application_number,
    development_description,
    development_address,
    development_postcode,
    itm_easting,
    itm_northing,
    application_status,
    application_type,
    decision,
    land_use_code,
    area_of_site,
    num_residential_units,
    one_off_house,
    floor_area,
    received_date,
    withdrawn_date,
    decision_date,
    decision_due_date,
    grant_date,
    expiry_date,
    appeal_ref_number,
    appeal_status,
    appeal_decision,
    appeal_decision_date,
    appeal_submitted_date,
    further_information_request_date,
    further_information_received_date,
    link_app_details,
    one_off_kpi,
    etl_date,
    site_id,
    shape_area,
    shape_length
)
SELECT
    NULLIF("OBJECTID", '')::bigint,
    NULLIF("PlanningAuthority", ''),
    NULLIF("ApplicationNumber", ''),
    NULLIF("DevelopmentDescription", ''),
    NULLIF("DevelopmentAddress", ''),
    NULLIF("DevelopmentPostcode", ''),

    NULLIF("ITMEasting", '')::numeric,
    NULLIF("ITMNorthing", '')::numeric,

    NULLIF("ApplicationStatus", ''),
    NULLIF("ApplicationType", ''),
    NULLIF("Decision", ''),
    NULLIF("LandUseCode", ''),

    NULLIF("AreaofSite", '')::numeric,
    NULLIF("NumResidentialUnits", '')::numeric,

    NULLIF("OneOffHouse", ''),

    NULLIF("FloorArea", '')::numeric,

    to_timestamp(NULLIF("ReceivedDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("WithdrawnDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("DecisionDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("DecisionDueDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("GrantDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("ExpiryDate", '')::numeric / 1000)::date,

    NULLIF("AppealRefNumber", ''),
    NULLIF("AppealStatus", ''),
    NULLIF("AppealDecision", ''),

    to_timestamp(NULLIF("AppealDecisionDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("AppealSubmittedDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("FIRequestDate", '')::numeric / 1000)::date,
    to_timestamp(NULLIF("FIRecDate", '')::numeric / 1000)::date,

    NULLIF("LinkAppDetails", ''),
    NULLIF("OneOffKPI", ''),

    to_timestamp(NULLIF("ETL_DATE", '')::numeric / 1000)::date,

    NULLIF("SiteId", ''),

    NULLIF("Shape__Area", '')::numeric,
    NULLIF("Shape__Length", '')::numeric

FROM raw.planning_applications;