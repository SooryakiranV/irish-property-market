CREATE TABLE IF NOT EXISTS raw.ppr_transactions (
   sale_date text,
   sale_year text,
   sale_month text,
   sale_quarter text,
   sale_year_month text,
   address text,
   county text,
   eircode text,
   price_eur text,
   not_full_market_price text,
   is_not_full_market_price text,
   vat_exclusive text,
   is_vat_exclusive text,
   property_description text,
   is_new_property text,
   is_second_hand_property text,
   property_size_description text,
   property_size_category text
);

CREATE TABLE IF NOT EXISTS raw.rppi_series (
   "Statistic Label" text,
   "Month" text,
   "Type of Residential Property" text,
   "UNIT" text,
   "VALUE" text,
   month text,
   year text,
   month_number text,
   quarter text,
   year_month text,
   property_series text,
   rppi_value text
);

CREATE TABLE IF NOT EXISTS raw.planning_applications (
   "OBJECTID" text,
   "PlanningAuthority" text,
   "ApplicationNumber" text,
   "DevelopmentDescription" text,
   "DevelopmentAddress" text,
   "DevelopmentPostcode" text,
   "ITMEasting" text,
   "ITMNorthing" text,
   "ApplicationStatus" text,
   "ApplicationType" text,
   "Decision" text,
   "LandUseCode" text,
   "AreaofSite" text,
   "NumResidentialUnits" text,
   "OneOffHouse" text,
   "FloorArea" text,
   "ReceivedDate" text,
   "WithdrawnDate" text,
   "DecisionDate" text,
   "DecisionDueDate" text,
   "GrantDate" text,
   "ExpiryDate" text,
   "AppealRefNumber" text,
   "AppealStatus" text,
   "AppealDecision" text,
   "AppealDecisionDate" text,
   "AppealSubmittedDate" text,
   "FIRequestDate" text,
   "FIRecDate" text,
   "LinkAppDetails" text,
   "OneOffKPI" text,
   "ETL_DATE" text,
   "SiteId" text,
   "Shape__Area" text,
   "Shape__Length" text
);

CREATE TABLE IF NOT EXISTS staging.ppr_transactions (
   ppr_id bigserial PRIMARY KEY,
   sale_date date NOT NULL,
   sale_year integer NOT NULL,
   sale_month integer NOT NULL,
   sale_quarter integer NOT NULL,
   sale_year_month char(7) NOT NULL,
   address text NOT NULL,
   county text NOT NULL,
   eircode text,
   price_eur numeric(14, 2) NOT NULL,
   not_full_market_price text,
   is_not_full_market_price boolean NOT NULL,
   vat_exclusive text,
   is_vat_exclusive boolean NOT NULL,
   property_description text,
   is_new_property boolean NOT NULL,
   is_second_hand_property boolean NOT NULL,
   property_size_description text,
   property_size_category text
);

CREATE TABLE IF NOT EXISTS staging.rppi_series (
   rppi_id bigserial PRIMARY KEY,
   statistic_label text,
   source_month_label text,
   residential_property_type text,
   unit text,
   source_value text,
   month_start date NOT NULL,
   year integer NOT NULL,
   month_number integer NOT NULL,
   quarter integer NOT NULL,
   year_month char(7) NOT NULL,
   property_series text NOT NULL,
   rppi_value numeric(10, 2)
);

CREATE TABLE IF NOT EXISTS staging.planning_applications (
   planning_id bigserial PRIMARY KEY,
   object_id bigint,
   planning_authority text,
   application_number text,
   development_description text,
   development_address text,
   development_postcode text,

   itm_easting numeric,
   itm_northing numeric,

   application_status text,
   application_type text,
   decision text,
   land_use_code text,

   area_of_site numeric,
   num_residential_units numeric,

   one_off_house text,
   floor_area numeric,

   received_date date,
   withdrawn_date date,
   decision_date date,
   decision_due_date date,
   grant_date date,
   expiry_date date,

   appeal_ref_number text,
   appeal_status text,
   appeal_decision text,
   appeal_decision_date date,
   appeal_submitted_date date,

   further_information_request_date date,
   further_information_received_date date,

   link_app_details text,
   one_off_kpi text,
   etl_date date,
   site_id text,

   shape_area numeric,
   shape_length numeric
);

CREATE TABLE IF NOT EXISTS analytics.monthly_market (
   year_month char(7) PRIMARY KEY,
   month_start date NOT NULL,
   transactions integer NOT NULL,
   total_value numeric(18, 2) NOT NULL,
   mean_price numeric(14, 2),
   median_price numeric(14, 2),
   national_rppi numeric(10, 2)
);

CREATE TABLE IF NOT EXISTS analytics.county_market (
   county text NOT NULL,
   sale_year integer NOT NULL,
   transactions integer NOT NULL,
   total_value numeric(18, 2) NOT NULL,
   mean_price numeric(14, 2),
   median_price numeric(14, 2),
   new_property_transactions integer NOT NULL,
   second_hand_property_transactions integer NOT NULL,
   PRIMARY KEY (county, sale_year)
);

CREATE TABLE IF NOT EXISTS analytics.planning_activity (
   planning_authority text NOT NULL,
   year_month char(7) NOT NULL,
   month_start date NOT NULL,
   applications integer NOT NULL,
   granted_applications integer NOT NULL,
   refused_applications integer NOT NULL,
   residential_units numeric(14, 2),
   PRIMARY KEY (planning_authority, year_month)
);

CREATE TABLE IF NOT EXISTS analytics.property_market_summary (
   metric_name text PRIMARY KEY,
   metric_value numeric(18, 2),
   metric_text text
);