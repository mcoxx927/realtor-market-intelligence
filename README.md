# Real Estate Market Intelligence Analysis

Automated pipeline for analyzing Redfin city-level market data with Python-generated strategic insights.

## Analysis Overview

- **Markets Analyzed:** Charlotte-Concord-Gastonia, NC-SC | Roanoke, VA
- **Data Source:** Redfin City Market Tracker (TSV format)
- **Time Period:** 2012-2025 (Historical data available)
- **Analysis Level:** Metro + City (Top 10 cities per metro)
- **Update Frequency:** Monthly

## Quick Start

### Monthly Workflow

1. **Download latest data from Redfin:**
New data will be released monthly during the Friday of the third full week of the month

https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz
	OR manually
https://www.redfin.com/news/data-center/
   - scroll to "Redfin Monthly Housing Market Data"
    - Click on "city" hyperlink in this section:
		Download region data here: National, Metro, State, County, City, Zip Code, Neighborhood
   - Get `city_market_tracker.tsv000.gz` from Redfin Data Center
   - Place in project root directory

2. **Run the complete pipeline:**
   ```bash
   python run_market_analysis.py
   ```

3. **Review the outputs:**
   - Enhanced HTML dashboards with interactive charts
   - JSON data files with 12-month historical trends
   - Strategic analysis summaries with market recommendations

## System Architecture

### Pipeline Components

```
city_market_tracker.tsv000.gz (918MB national file)
           ↓
[Step 1] extract_metros.py
           - Reads metro_config.json
           - Extracts Charlotte, Roanoke, + configurable metros
           ↓
charlotte_cities_filtered.tsv + roanoke_cities_filtered.tsv
           ↓
[Step 2] process_market_data.py
           - Processes last 12 months of data
           - Calculates health scores
           - Identifies top 10 cities
           ↓
charlotte_data.json + roanoke_data.json
           ↓
[Step 3] generate_dashboards_v2.py
           - Enhanced HTML with interactive charts
           - Dropdown selectors for metrics
           - Top 5 city historical trends
           ↓
dashboard_enhanced_[metro]_YYYY-MM.html
           ↓
[Step 4] extract_summary.py
           - Classifies markets (BULLISH/NEUTRAL/BEARISH)
           - Generates seller/buyer/investor recommendations
           - Identifies alert cities with severity levels
           ↓
[metro]_summary.json (strategic analysis + recommendations)
```

---

## Files and Configuration

### Configuration Files

**metro_config.json** - Define which metros to analyze
```json
{
  "metros": [
    {
      "name": "charlotte",
      "display_name": "Charlotte, NC",
      "metro_code": "16740",
      "enabled": true
    }
  ]
}
```

### Python Scripts

1. **extract_metros.py** - Extracts metros from raw national TSV file
2. **process_market_data.py** - Processes TSV into JSON with 12-month trends
3. **generate_dashboards_v2.py** - Generates enhanced HTML dashboards
4. **extract_summary.py** - Generates strategic analysis with recommendations
5. **run_market_analysis.py** - Master script that runs all four steps in sequence

### Output Structure

```
charlotte/
└── YYYY-MM/
    ├── charlotte_data.json                          (12-month trends)
    ├── dashboard_enhanced_charlotte_YYYY-MM.html    (Interactive charts)
    └── charlotte_summary.json                       (Strategic analysis + recommendations)

roanoke/
└── YYYY-MM/
    ├── roanoke_data.json                            (12-month trends)
    ├── dashboard_enhanced_roanoke_YYYY-MM.html      (Interactive charts)
    └── roanoke_summary.json                         (Strategic analysis + recommendations)
```

**Note:** YYYY-MM folder is determined dynamically from the data period, not hardcoded.

---

## Dashboard Features

### Enhanced HTML Dashboards

The generated dashboards include:

**1. Metro Inventory Dynamics Chart**
- Dropdown to toggle between Active/New/Pending listings
- 12-month historical trends

**2. Price Reductions Chart**
- Bar chart showing properties with price cuts

**3. DOM + Pending Ratio Chart**
- Dual Y-axis chart with 12-month trends

**4. Top 5 Cities Historical Trends**
- City selector dropdown (choose which city to view)
- Metric selector dropdown (Inventory/Sales/DOM/Price)
- Shows ONE metric at a time for proper scaling

**5. Top 10 Cities Table**
- Current month snapshot with health scores

---

## Strategic Analysis Summary

The `{metro}_summary.json` file contains Python-generated market analysis:

### Market Classification
- **Market Status:** BULLISH / SLIGHTLY_BULLISH / NEUTRAL / SLIGHTLY_BEARISH / BEARISH
- **Market Description:** Human-readable summary of market conditions
- **Health Score:** 0-100 rating of market strength

### City Tiers
Cities are automatically classified into three market tiers:
- **HOT Markets:** Strong seller advantage, high demand
- **BALANCED Markets:** Equilibrium between buyers and sellers
- **BUYER Markets:** Buyer advantage, excess inventory

### Recommendations by Role
Strategic guidance provided for:
- **Sellers:** Pricing strategy and timeline expectations
- **Buyers:** Negotiating approach and market conditions
- **Investors:** Strategy focus (appreciation vs. cash flow)

### Alert Cities
Cities with concerning metrics identified and ranked by severity:
- **HIGH:** Significant inventory surges, major price declines
- **MEDIUM:** Emerging issues, requires monitoring
- **LOW:** Minor concerns, standard approach sufficient

Each alert includes specific recommendations for action.

---

## Adding New Metros

To add a new metro area (e.g., Austin, TX):

1. **Find the metro code:**
   - Look up PARENT_METRO_REGION_METRO_CODE in Redfin data
   - Example: Austin = 12420

2. **Edit metro_config.json:**
   ```json
   {
     "name": "austin",
     "display_name": "Austin, TX",
     "metro_code": "12420",
     "enabled": true
   }
   ```

3. **Run the pipeline:**
   ```bash
   python run_market_analysis.py
   ```

**No code changes required!**

---

## Requirements

Python packages:
```bash
pip install pandas
```

Dashboards use CDN for TailwindCSS and Chart.js (no local install needed).

---

## Data Sources

**Source:** Redfin Data Center
- URL: https://www.redfin.com/news/data-center/
- File: city_market_tracker.tsv000.gz (918MB, updated monthly)
- Coverage: National (all US metros)
- History: 2012-present
- Metrics: ~58 fields per city-month-property type

**Current Metros Analyzed:**
- Charlotte-Concord-Gastonia, NC-SC (Metro Code: 16740)
  - 105 cities available, 78 in top 10 analysis, 2,486 sales (Oct 2025)

- Roanoke, VA (Metro Code: 40220)
  - 24 cities available, 16 in top 10 analysis, 242 sales (Oct 2025)

---

**Last Updated:** December 15, 2025
**Pipeline Version:** 2.1 (Dynamic dates + Python-generated strategic analysis)
