# Real Estate Market Intelligence Analysis

Automated pipeline for analyzing Redfin city-level market data with AI-powered strategic insights.

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

4. **Invoke the AI agent for strategic analysis:**
   - The agent will read the JSON files and generate strategic reports

## System Architecture

### Pipeline Components

```
city_market_tracker.tsv000.gz (918MB national file)
           ↓
    extract_metros.py
    - Reads metro_config.json
    - Extracts Charlotte, Roanoke, + configurable metros
           ↓
charlotte_cities_filtered.tsv + roanoke_cities_filtered.tsv
           ↓
    process_market_data.py
    - Processes last 12 months of data
    - Calculates health scores
    - Identifies top 10 cities
           ↓
charlotte_data.json + roanoke_data.json
           ↓
    generate_dashboards_v2.py
    - Enhanced HTML with interactive charts
    - Dropdown selectors for metrics
    - Top 5 city historical trends
           ↓
dashboard_enhanced_[metro]_2025-09.html
           ↓
    AI Agent (Real-Estate-Market-Intelligence-Agent)
    - Reads JSON files
    - Generates strategic analysis reports
           ↓
metro_report_[metro]_2025-09.md + city_alerts_[metro]_2025-09.md
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
4. **run_market_analysis.py** - Master script that runs all three in sequence

### Output Structure

```
charlotte/
├── 2025-09/
│   ├── charlotte_data.json                          (12-month trends)
│   ├── dashboard_enhanced_charlotte_2025-09.html    (Interactive charts)
│   ├── metro_report_charlotte_2025-09.md            (AI strategic analysis)
│   └── city_alerts_charlotte_2025-09.md             (AI flagged cities)
```

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
  - 82 cities analyzed, 2,475 sales (Sep 2025)

- Roanoke, VA (Metro Code: 40220)
  - 17 cities analyzed, 243 sales (Sep 2025)

---

**Last Updated:** October 19, 2025
**Pipeline Version:** 2.0 (Enhanced with metro extraction + flexible configuration)
