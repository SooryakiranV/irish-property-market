# Data Sources

## 1. Residential Property Price Register (PPR)

**Source:** Property Services Regulatory Authority / Residential Property Price Register

**Role:** Primary transaction-level property dataset.

The PPR provides residential property sale records in Ireland, including sale date, address, county, Eircode where available, transaction price, property description and related indicators.

The dataset is used as the primary source for:
- Property transaction volumes
- Transaction values
- Mean and median transaction prices
- County-level market analysis
- New versus second-hand property analysis
- Historical market trends

**Project status:** Investigated, ingested, cleaned, validated and loaded into PostgreSQL.

---

## 2. CSO Residential Property Price Index (RPPI)

**Source:** Central Statistics Office (CSO)

**Role:** Independent property-price benchmark.

The CSO Residential Property Price Index is used alongside PPR transaction data to provide a standardised benchmark for property-price evolution over time.

The RPPI is not treated as a duplicate transaction dataset. It provides an independent index-based view of the Irish residential property market.

**Project status:** Investigated, ingested, validated and loaded into PostgreSQL.

---

## 3. National Planning Applications Dataset

**Source:** Department of Housing, Local Government and Heritage / data.gov.ie

**Role:** Planning and development activity dataset.

The dataset contains planning application records including planning authority, application details, dates, decisions and residential-unit information where available.

It is used for:
- Planning application volumes
- Granted and refused applications
- Residential units associated with applications
- Planning activity over time
- Planning-authority analysis
- Comparison of planning activity with property-market indicators

Planning applications are analysed as an independent dataset and are not joined to individual PPR transactions.

**Project status:** Investigated, ingested, cleaned, validated and loaded into PostgreSQL.

---

## Source Integration

The three sources provide complementary perspectives:

| Source | Analytical role |
|---|---|
| PPR | Property transactions |
| CSO RPPI | Property-price index benchmark |
| Planning Applications | Development and planning activity |

The datasets are integrated at appropriate analytical levels such as time and geography rather than treating records from different sources as one-to-one matches.