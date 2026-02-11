# Distressed Proxy Automation Playbook

Last updated: 2026-02-11

## Goal
Create a repeatable pipeline to populate:
- `market_radar/inputs/competition_proxy.csv`
- `market_radar/inputs/housing_age_proxy.csv`

for use by:
- `python3 market_radar/run_distressed_fit.py`

This design keeps your current scoring pipeline intact and adds proxy enrichment in a controlled way.

---

## Why This Design
Your business model needs three things that plain market health misses:
1. Acquisition-side pressure/opportunity (distress + weak demand pockets)
2. Rehab complexity risk (older stock profile)
3. Dispo depth vs acquisition competition (active investor + marketer intensity)

This playbook does that with 4 scripts and two refresh cadences:
- Monthly: competition proxies
- Annual: housing age proxies

---

## The 4 Scripts (Concept + I/O)

## 1) `scripts/proxy/refresh_competition_places.py`
Purpose:
- Pull a competition-visibility proxy from Google Places API for markets in current top 20 (+ prior top 20 for stability).

Inputs:
- `market_radar/outputs_distressed_fit/YYYY-MM/distressed_fit_ranked.csv`
- `market_radar/seeds_roanoke_4hr.csv` (for `metro_code`, `display_name`, `lat`, `lon`)
- Env: `GOOGLE_MAPS_API_KEY`

Method:
- Query Places Text Search (New) using phrase set:
  - `we buy houses`
  - `cash home buyers`
  - `sell house fast`
  - `real estate investor`
  - `home buying company`
- Use location bias around metro centroid (`lat/lon` from seed) and pagination token to collect multiple pages.
- Deduplicate by `place_id`.
- Produce weighted count metric per metro:
  - `active_wholesalers = unique_place_id_count_weighted`

Outputs:
- `market_radar/inputs/intermediate/competition_places_raw_YYYY-MM-DD.jsonl`
- `market_radar/inputs/intermediate/competition_places_agg_YYYY-MM-DD.csv`

Notes:
- Use Places API (not Google Business Profile API) for discovery.
- Persist only allowed fields and respect Places API policies.

## 2) `scripts/proxy/refresh_google_ads_cpc.py`
Purpose:
- Pull CPC/competition pressure automatically from Google Ads API for target metros and keyword set.

Inputs:
- `market_radar/outputs_distressed_fit/YYYY-MM/distressed_fit_ranked.csv` (top 20 metros to enrich)
- `market_radar/seeds_roanoke_4hr.csv` (for `metro_code`, market names)
- `market_radar/inputs/geo/google_ads_geo_targets.csv` (CBSA/county to Google geo target IDs)
- Env/credentials:
  - `GOOGLE_ADS_DEVELOPER_TOKEN`
  - OAuth client credentials and refresh token
  - `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
  - `GOOGLE_ADS_CUSTOMER_ID`

Method:
- Use Google Ads API `KeywordPlanIdeaService.GenerateKeywordHistoricalMetrics`.
- Query keyword set:
  - `we buy houses`
  - `cash home buyers`
  - `sell house fast`
  - `sell my house as is`
  - `cash offer for my house`
- Use metro geo target when available; fallback to county geo targets.
- Compute per-metro CPC proxy:
  - `ppc_cpc_sell_house_fast = median(top_of_page_bid_high)` across keywords.

Outputs:
- `market_radar/inputs/intermediate/google_ads_cpc_raw_YYYY-MM-DD.jsonl`
- `market_radar/inputs/intermediate/google_ads_cpc_agg_YYYY-MM-DD.csv`

Important:
- Google Ads API is not API-key-only. It requires developer token + OAuth + customer context.

## 3) `scripts/proxy/refresh_housing_age.py`
Purpose:
- Annual refresh of housing age profile by metro (CBSA).

Inputs:
- Census ACS 5-year API (table group `B25034`)
- `market_radar/seeds_roanoke_4hr.csv`

Output schema (`housing_age_proxy.csv`):
- `metro_code`
- `market`
- `pct_pre_1980`
- `pct_pre_1940`
- `historic_district_share`
- `source`
- `updated_at`
- `confidence`

Rules:
- Use ACS 5-year estimates for reliability and full geography coverage.
- Start `historic_district_share` as blank/`null` if no reliable source is wired.

## 4) `scripts/proxy/build_and_validate_proxy_csvs.py`
Purpose:
- Merge all available proxy inputs and enforce quality gates before scoring.

Inputs:
- `market_radar/inputs/intermediate/competition_places_agg_YYYY-MM-DD.csv`
- `market_radar/inputs/intermediate/google_ads_cpc_agg_YYYY-MM-DD.csv`
- `market_radar/inputs/manual/propstream_cash_buyers_180d.csv`
- `market_radar/inputs/housing_age_proxy.csv`

Required columns:
- PropStream file:
  - `metro_code`
  - `active_cash_buyers` (rolling 180d)

Outputs:
- `market_radar/inputs/competition_proxy.csv`
- `market_radar/inputs/validation/proxy_validation_YYYY-MM-DD.json`

Checks:
- Every seeded `metro_code` appears at most once per file.
- No duplicate `metro_code`.
- Range checks:
  - `pct_*` in `[0,1]`
  - count fields `>=0`
  - CPC `>=0`
- Freshness checks:
  - competition <= 45 days old
  - housing age <= 400 days old
- Coverage warnings:
  - if top 20 is missing any competition fields, fail pipeline.

---

## Google Ads API CPC Process (Primary Monthly)

Primary reference pages:
- Google Ads API historical metrics docs
- Google Ads API OAuth flow docs

Prerequisites:
- Google Ads manager access + active customer account.
- Approved developer token.
- OAuth client credentials and refresh token.
- Geo target ID mapping file for your metros.

Automation workflow (monthly):
1. Read current top 20 metros from distressed-fit output.
2. Map each metro to one or more Google geo target IDs.
3. Request historical metrics for your keyword set.
4. Save raw API responses for audit.
5. Aggregate per metro:
   - median high top-of-page bid
   - median low top-of-page bid
   - average monthly searches (optional signal)
6. Write aggregated file for merge step.

Recommended aggregated columns:
- `metro_code`
- `ppc_cpc_sell_house_fast`
- `top_of_page_bid_low_med`
- `top_of_page_bid_high_med`
- `avg_monthly_searches_total`
- `extracted_at`

Normalization rule for `ppc_cpc_sell_house_fast`:
- Use the median of `top_of_page_bid_high` across the five core keywords for each metro.
- If fewer than 3 keywords have valid bids, set confidence low and flag in validation.

## Keyword Planner UI Fallback (Manual)
If API credentials are temporarily unavailable, pull from Keyword Planner UI and create:
- `market_radar/inputs/intermediate/google_ads_cpc_agg_YYYY-MM-DD.csv`

UI steps remain:
1. Tools -> Planning -> Keyword Planner.
2. Get search volume and forecasts.
3. Use the same keyword set and metro targeting.
4. Export and map to the aggregated columns above.

---

## Exact Housing Stock Process via Census ACS (Annual)

Primary reference pages:
- ACS guidance on 1-year vs 5-year estimates
- ACS API groups and geography docs
- Table `B25034` variable list

### Why ACS 5-year
Use ACS 5-year because:
- includes all geographies (including smaller metros)
- more reliable sample size than 1-year

### Geography match strategy (important)
Redfin `metro_code` appears to align with CBSA 5-digit codes (inference validated on known metros like 40220 Roanoke, 16740 Charlotte).

Implementation rule:
- Treat `metro_code` as CBSA code for ACS queries.
- Validate by checking names against ACS `NAME` and Redfin display names.
- If mismatch, log exception file and require manual mapping override.

### ACS table and formulas
Use table group `B25034` (Year Structure Built):
- `B25034_001E` total housing units
- `B25034_007E` built 1970-1979
- `B25034_008E` built 1960-1969
- `B25034_009E` built 1950-1959
- `B25034_010E` built 1940-1949
- `B25034_011E` built 1939 or earlier

Compute:
- `pct_pre_1980 = (B25034_007E + B25034_008E + B25034_009E + B25034_010E + B25034_011E) / B25034_001E`
- `pct_pre_1940 = B25034_011E / B25034_001E`
- `historic_district_share = null` (until source added)

### ACS API query pattern
Dataset:
- `https://api.census.gov/data/{year}/acs/acs5`

Geography:
- `for=metropolitan statistical area/micropolitan statistical area:{cbsa_code}`

Example variable list:
- `NAME,B25034_001E,B25034_007E,B25034_008E,B25034_009E,B25034_010E,B25034_011E`

Add API key for production reliability:
- `&key=YOUR_CENSUS_API_KEY`

### Annual schedule
- Refresh once per year after ACS 5-year release.
- Keep previous file as fallback until validation passes.

---

## Redfin Granularity Expansion (Recommended)

You already use city-level Redfin data. Redfin publishes equivalent monthly datasets for:
- Metro
- State
- County
- City
- Zip Code
- Neighborhood

Use these official files to sharpen top-20 market diagnostics:
- `zip_code_market_tracker.tsv000.gz`
- `neighborhood_market_tracker.tsv000.gz`
- optionally `county_market_tracker.tsv000.gz`

Direct monthly download links:
- `https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/metro_market_tracker.tsv000.gz`
- `https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/state_market_tracker.tsv000.gz`
- `https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/county_market_tracker.tsv000.gz`
- `https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz`
- `https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/zip_code_market_tracker.tsv000.gz`
- `https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/neighborhood_market_tracker.tsv000.gz`

Practical use:
- For top 20 metros, derive concentration stats (by zip/neighborhood):
  - share of activity in your buy box
  - tails of DOM and price volatility
  - pockets likely to generate distressed leads vs rehab blowups

## Augmenting `core_markets/` with Zip + Neighborhood Intelligence

Goal:
- Keep existing metro summary/narrative flow, but inject a granular layer so each monthly narrative and recommendation references where risk/opportunity is concentrated.

Proposed implementation path:
1. Add `extract_granular_submarkets.py`:
   - Pull zip and neighborhood Redfin trackers.
   - Filter rows by target `PARENT_METRO_REGION_METRO_CODE`.
   - Compute monthly metrics at submarket level.
2. Add `process_granular_submarkets.py`:
   - Compute submarket health proxies:
     - price trend stability
     - DOM pressure
     - inventory expansion/contraction
     - pending-sales momentum
   - Flag:
     - `distress_opportunity_zones`
     - `rehab_risk_zones`
     - `liquidity_zones`
3. Write new per-metro artifact:
   - `core_markets/{metro}/{YYYY-MM}/{metro}_granular.json`
4. Update `extract_summary.py` (or add `extract_summary_granular.py`) to include:
   - top 5 opportunity zips/neighborhoods
   - top 5 avoid/slow pockets
   - concentration metrics (share of metro volume in top pockets)
5. Update `ai_narrative.py` prompt payload to consume granular artifact:
   - Keep city-level mentions for readability.
   - Add submarket concentration statements using zips/neighborhoods only when data quality is high.

Quality controls for granular layer:
- Minimum transaction threshold per zip/neighborhood (for example 8-10 sales/month).
- Winsorize extreme percent changes to avoid tiny-denominator distortions.
- Tag each hotspot with confidence level.

Why this helps:
- Core metro narrative becomes actionable for acquisitions/dispo routing.
- Distressed-fit top 20 can be quickly translated into specific hunt zones.

---

## Source Fit Assessment (from research)

Best-fit primary sources for your exact proxy needs:
1. Redfin monthly trackers (metro/county/city/zip/neighborhood) -> best local market structure coverage
2. Census ACS 5-year B25034 -> best annual housing-age stock signal
3. Google Places API (Text Search New) -> best automated competition-visibility proxy
4. PropStream 180d export -> best direct investor/cash-buyer activity input (manual for now)
5. Google Ads API historical metrics -> best CPC competition pressure input (automation-first)

Useful but secondary:
- HUD USPS Crosswalk -> useful when converting ZIP-level sources to CBSA
- FHFA HPI -> good trend benchmark, not a distress or competition input

Low-fit for this specific model:
- NAHB indexes (higher-level construction/remodel sentiment)
- Fannie Mae HPSI/NHS (consumer sentiment, mostly national)

---

## Monthly Operating Runbook (Operator)

1. Run first-pass distressed ranking (base):
   - `python3 market_radar/run_distressed_fit.py`
2. Refresh competition Places for top 20:
   - `python3 scripts/proxy/refresh_competition_places.py`
3. Refresh CPC via Google Ads API for top 20:
   - `python3 scripts/proxy/refresh_google_ads_cpc.py`
4. Admin drops PropStream file:
   - `market_radar/inputs/manual/propstream_cash_buyers_180d.csv`
5. Build and validate proxy CSVs:
   - `python3 scripts/proxy/build_and_validate_proxy_csvs.py`
6. Final enriched ranking:
   - `python3 market_radar/run_distressed_fit.py --with-backtest`

Annual add-on:
- `python3 scripts/proxy/refresh_housing_age.py`

Core-markets granular add-on (monthly):
- `python3 extract_granular_submarkets.py`
- `python3 process_granular_submarkets.py`
- then normal `extract_summary.py` / `ai_narrative.py`

---

## Handoff Checklist for a Fresh Session

When restarting this work, provide:
- This file: `docs/DISTRESSED_PROXY_AUTOMATION_PLAYBOOK.md`
- Current seed file: `market_radar/seeds_roanoke_4hr.csv`
- Latest output: `market_radar/outputs_distressed_fit/YYYY-MM/distressed_fit_ranked.csv`
- A sample PropStream export (180d)
- Google Ads API credentials (developer token, OAuth client, refresh token, customer IDs)
- Any API keys available (Census, Google Maps/Places)
- If API is not wired yet: a sample Keyword Planner export as temporary fallback

Then implementation can be executed directly with minimal re-discovery.

---

## References (Primary)
- Redfin Data Center monthly downloads (metro/state/county/city/zip/neighborhood): https://www.redfin.com/news/data-center/
- Redfin metrics definitions: https://www.redfin.com/news/data-center-metrics-definitions/
- Redfin investor data page: https://www.redfin.com/news/data-center/investor-data/
- Google Business Profile overview (management of your own listings): https://developers.google.com/my-business/content/overview
- Google Places Text Search (New): https://developers.google.com/maps/documentation/places/web-service/text-search
- Places API usage and billing: https://developers.google.com/maps/documentation/places/web-service/usage-and-billing
- Places API policies: https://developers.google.com/maps/documentation/places/web-service/policies
- Google Ads Help - Use Keyword Planner: https://support.google.com/google-ads/answer/7337243
- Google Ads Help - Refine keywords in Keyword Planner: https://support.google.com/google-ads/answer/6325025
- Google Ads API historical metrics: https://developers.google.com/google-ads/api/docs/keyword-planning/generate-historical-metrics
- Google Ads API OAuth (installed/web app): https://developers.google.com/google-ads/api/docs/oauth/overview
- Google Ads API auth and config: https://developers.google.com/google-ads/api/docs/get-started/introduction
- Census ACS 1-year vs 5-year guidance: https://www.census.gov/programs-surveys/acs/guidance/estimates.html
- Census ACS API groups list: https://api.census.gov/data/2024/acs/acs1/groups.html
- Census ACS B25034 variables (example): https://api.census.gov/data/2021/acs/acs5/groups/B25034.html
- Census API geography (includes geo level 310 metro/micro): https://api.census.gov/data/2024/acs/acs5/profile/geography.html
- Census metro/micro delineation files: https://www.census.gov/programs-surveys/metro-micro/about/delineation-files.html
- HUD USPS Crosswalk overview/API: https://www.huduser.gov/portal/datasets/usps_crosswalk.html
- FHFA HPI datasets: https://www.fhfa.gov/house-price-index
- NAHB Home Building Geography Index: https://www.nahb.org/News-and-Economics/Housing-Economics/Indices/Home-Building-Geography-Index
- Fannie Mae HPSI/NHS (example release): https://www.fanniemae.com/newsroom/fannie-mae-news/overall-housing-confidence-rising-home-prices-influence-increasingly-divergent-home-buying-and
