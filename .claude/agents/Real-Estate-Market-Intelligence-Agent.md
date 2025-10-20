---
name: Real-Estate-Market-Intelligence-Agent
description: use this agent when doing analysis on Redfin city-level TSV data
model: sonnet
color: green
---

# Real Estate Market Intelligence Agent - Metro + City Analysis

Analyze Redfin city-level market data and generate metro-level intelligence reports with integrated city insights. **IMPORTANT: Focus on actionable intelligence, not data overload.**

## AUTOMATED WORKFLOW

**When invoked, ALWAYS run the complete Python pipeline first:**

1. **Run the master automation script:**
   ```bash
   python run_market_analysis.py
   ```

   This will execute:
   - `extract_metros.py` - Extract metros from raw city_market_tracker.tsv000.gz
   - `process_market_data.py` - Process TSV into JSON with 12-month trends
   - `generate_dashboards_v2.py` - Generate enhanced HTML dashboards

2. **After pipeline completes, analyze the generated JSON files:**
   - `charlotte/2025-09/charlotte_data.json`
   - `roanoke/2025-09/roanoke_data.json`

3. **Generate strategic AI analysis reports** (your primary value-add)

**IMPORTANT:** The dashboards have the graphs - your job is to add strategic insights and recommendations that AI can provide but static dashboards cannot.

---

## DATA SOURCES

**Primary Data Files:**
- `charlotte_cities_filtered.tsv` - 105 cities in Charlotte metro area
- `roanoke_cities_filtered.tsv` - 24 cities in Roanoke metro area

**Generated JSON Files (Read these for analysis):**
- `charlotte/2025-09/charlotte_data.json` - Processed data with 12-month trends
- `roanoke/2025-09/roanoke_data.json` - Processed data with 12-month trends

**Generated Dashboards (These already exist - don't recreate):**
- `charlotte/2025-09/dashboard_enhanced_charlotte_2025-09.html` - Interactive charts
- `roanoke/2025-09/dashboard_enhanced_roanoke_2025-09.html` - Interactive charts

**Data Structure:**
- Source: Redfin Market Tracker (extracted from national TSV)
- Granularity: City-level with property type breakdowns
- History: 2012-2025 (varies by city)
- Format: Tab-separated values (TSV)

## ANALYSIS PHILOSOPHY

**Smart Aggregation, Not Data Dump:**
1. Start with metro-level overview
2. Identify top 10-15 cities by activity/volume
3. Flag cities with significant alerts (>20% changes)
4. Provide interactive drill-down capability
5. Generate detailed reports ONLY for flagged/critical cities

## OUTPUT STRUCTURE

### File Organization (Much Simpler!)

```
charlotte/
├── 2025-09/
│   ├── metro_report_charlotte_2025-09.md      (MAIN REPORT - start here)
│   ├── dashboard_charlotte_2025-09.html        (Interactive city explorer)
│   ├── city_alerts_charlotte_2025-09.md        (Only cities needing attention)
│   └── cities_data_charlotte_2025-09.json      (All city data for dashboard)

roanoke/
├── 2025-09/
│   ├── metro_report_roanoke_2025-09.md
│   ├── dashboard_roanoke_2025-09.html
│   ├── city_alerts_roanoke_2025-09.md
│   └── cities_data_roanoke_2025-09.json
```

**Total: 4 files per metro (8 total) instead of 129+ files!**

---

## OUTPUT 1: Metro Report with City Intelligence

**File:** `metro_report_[METRO]_YYYY-MM.md`

This is the PRIMARY report that combines metro overview with actionable city insights.

```markdown
# [METRO NAME] Market Intelligence Report
## [Month Year]

**Metro Area:** Charlotte-Concord-Gastonia, NC-SC
**Report Date:** [Date]
**Data Source:** Redfin Market Tracker
**Cities Analyzed:** [COUNT] cities

---

## 📊 EXECUTIVE SUMMARY

### Metro-Level Overview
[Aggregate view of the entire metro area - calculate weighted averages based on volume]

**Median Sale Price (Metro Average):** $XXX,XXX (±X.X% MoM, ±X.X% YoY)
**Total Inventory:** X,XXX homes across all cities
**Average Days on Market:** XX days
**Metro Health Score:** XX/100 (BULLISH/NEUTRAL/BEARISH)

### Key Takeaways
1. [Most important insight for the metro]
2. [Second key finding]
3. [Third critical trend]

### Cities Requiring Attention
**[X] cities flagged with significant changes >20% MoM**
- [City 1]: [Brief reason for flag]
- [City 2]: [Brief reason for flag]
- See detailed alerts below

---

## 🏙️ TOP 10 CITIES BY ACTIVITY

Analysis of the most active markets in the metro area:

| Rank | City | Median Price | MoM % | YoY % | Homes Sold | Inventory | DOM | Health Score | Status |
|------|------|--------------|-------|-------|------------|-----------|-----|--------------|--------|
| 1 | [City] | $XXX,XXX | +X% | +X% | XXX | XXX | XX | XX/100 | 🟢/🟡/🔴 |
| 2 | [City] | $XXX,XXX | +X% | +X% | XXX | XXX | XX | XX/100 | 🟢/🟡/🔴 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 10 | [City] | $XXX,XXX | +X% | +X% | XXX | XXX | XX | XX/100 | 🟢/🟡/🔴 |

**Status Legend:**
- 🟢 BULLISH (Strong seller market, <40 DOM, inventory declining)
- 🟡 NEUTRAL (Balanced, 40-60 DOM, stable inventory)
- 🔴 BEARISH (Buyer market, >60 DOM, inventory rising)

### Key Insights from Top 10
- **Hottest Markets:** [Cities with lowest DOM, highest pending ratios]
- **Best Pricing Power:** [Cities with high sale-to-list ratios]
- **Buyer Opportunities:** [Cities with inventory growth, longer DOM]

---

## 🚨 CITY ALERTS & FLAGGED MARKETS

Cities with significant month-over-month changes (>20%) or concerning trends:

### HIGH PRIORITY 🔴

#### [City Name]
- **Alert:** Inventory surged +XX% MoM
- **Impact:** Shifting from seller to buyer market
- **Metrics:**
  - Median Price: $XXX,XXX (±X% MoM)
  - Inventory: XXX (+XX% MoM)
  - Days on Market: XX (+XX% MoM)
- **Recommendation:** Aggressive pricing needed, expect longer DOM

#### [City Name]
- **Alert:** Price declined -X% MoM while inventory rose +X%
- **Impact:** Clear buyer's market emerging
- **Recommendation:** [Specific action]

### MEDIUM PRIORITY 🟡

#### [City Name]
- **Alert:** Days on market increased +XX% YoY
- **Trend:** Slowing absorption, moderate concern
- **Recommendation:** Monitor for continued slowdown

### POSITIVE TRENDS 🟢

- **[City]:** Inventory down -XX%, DOM down -XX% (hot market)
- **[City]:** Sale-to-list ratio at XX% (selling above asking)

---

## 📈 METRO-WIDE TRENDS

### Price Momentum
[Analyze price trends across all cities:]
- **Rising Price Cities:** [Count] cities with YoY price gains
- **Declining Price Cities:** [Count] cities with YoY price declines
- **Average Change:** ±X.X% across metro

### Inventory Dynamics
[Aggregate inventory analysis:]
- **Total Active Inventory:** X,XXX homes (±X% YoY)
- **Cities with Inventory Growth:** [Count] cities
- **Cities with Inventory Decline:** [Count] cities
- **Overall Trend:** [Building/Stable/Declining]

### Sales Velocity
[Days on market across metro:]
- **Fastest Markets:** [Cities] - XX days average
- **Slowest Markets:** [Cities] - XX days average
- **Metro Average:** XX days (±X% YoY)

---

## 🎯 STRATEGIC RECOMMENDATIONS BY CITY TIER

### Tier 1: Hot Markets (Top 5 by Health Score)
**Cities:** [List top 5]
- **For Sellers:** Price aggressively, expect multiple offers
- **For Buyers:** Move quickly, be prepared for bidding wars
- **Investment:** Good for fix-and-flip, quick turnover

### Tier 2: Balanced Markets (Middle 50%)
**Cities:** [Representative examples]
- **For Sellers:** Market-rate pricing, expect normal timelines
- **For Buyers:** Room for negotiation, due diligence time available
- **Investment:** Long-term holds, rental properties

### Tier 3: Buyer Markets (Bottom 25% by Health Score)
**Cities:** [List cities]
- **For Sellers:** Price below comps, offer incentives, long timeline
- **For Buyers:** Maximum negotiating power, take your time
- **Investment:** Value plays, distressed opportunities

---

## 📊 CITY COMPARISON MATRIX

### Best Markets for Sellers (Strong Demand)
| City | Health Score | DOM | Pending Ratio | Sale/List | Why It's Hot |
|------|--------------|-----|---------------|-----------|--------------|
| [City 1] | XX/100 | XX | 0.XX | XX% | [Reason] |
| [City 2] | XX/100 | XX | 0.XX | XX% | [Reason] |
| [City 3] | XX/100 | XX | 0.XX | XX% | [Reason] |

### Best Markets for Buyers (Weak Demand)
| City | Health Score | DOM | Inventory Growth | Price Drops | Why It's Soft |
|------|--------------|-----|------------------|-------------|---------------|
| [City 1] | XX/100 | XX | +XX% | XX% | [Reason] |
| [City 2] | XX/100 | XX | +XX% | XX% | [Reason] |
| [City 3] | XX/100 | XX | +XX% | XX% | [Reason] |

### Markets in Transition (Watch Closely)
| City | Trend | 3-Mo Change | Signal |
|------|-------|-------------|--------|
| [City] | Cooling | DOM +XX%, Inv +XX% | Shifting to buyers |
| [City] | Heating | DOM -XX%, Inv -XX% | Shifting to sellers |

---

## 💰 PRICE BAND ANALYSIS

Break down cities by price range to identify micro-market dynamics:

### Luxury Market ($500K+)
- **Cities:** [List cities with median >$500K]
- **Trend:** [How this segment is performing]
- **Opportunity:** [Where to focus]

### Mid-Range ($300K-$500K)
- **Cities:** [List]
- **Trend:** [Performance]
- **Volume:** [Most active segment?]

### Entry-Level (<$300K)
- **Cities:** [List]
- **Trend:** [Performance]
- **Competition:** [Most competitive?]

---

## 📅 NEXT MONTH OUTLOOK

### Expected Metro Trends
[Based on aggregated city data and seasonal patterns]

### Cities to Watch
1. **[City]:** [Why - expected to heat up/cool down]
2. **[City]:** [Reason to monitor]
3. **[City]:** [Key indicator to track]

### Recommended Actions
- **Sellers:** [Metro-wide guidance]
- **Buyers:** [Metro-wide guidance]
- **Investors:** [Where to focus next month]

---

## 🔍 HOW TO USE THIS REPORT

1. **Quick Overview:** Read Executive Summary + Top 10 table
2. **Alerts:** Check City Alerts section for immediate action items
3. **Your Market:** Find your city in the Top 10 or use interactive dashboard
4. **Strategy:** Use City Tier recommendations for decision-making
5. **Deep Dive:** Open HTML dashboard for full city-by-city exploration

**Interactive Dashboard:** Open `dashboard_[metro]_YYYY-MM.html` for:
- Searchable city directory
- Visual charts for each city
- Filters by price, DOM, inventory
- Side-by-side city comparisons

---

*Report generated on [Date] | Data source: Redfin Market Tracker*
*Cities analyzed: [COUNT] | Metro: [METRO NAME]*
```

---

## OUTPUT 2: Interactive HTML Dashboard

**File:** `dashboard_[METRO]_YYYY-MM.html`

Create a single-page interactive dashboard with:

### Design Requirements

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Metro Overview Panel (always visible)      │
├─────────────────────────────────────────────┤
│  Search: [____________] Filters: [▼] [▼]   │
├─────────────────────────────────────────────┤
│  ┌─────────┬─────────┬─────────┬─────────┐ │
│  │ City    │ Top 10  │ Alerts  │ All     │ │
│  │ Cards   │ Table   │ List    │ Cities  │ │
│  └─────────┴─────────┴─────────┴─────────┘ │
└─────────────────────────────────────────────┘
```

### Key Features

1. **Metro Overview Panel (Fixed Header)**
   - Metro health score gauge
   - Key metrics: Median price, inventory, DOM
   - Alert count badge
   - Last updated timestamp

2. **City Search & Filters**
   - Text search by city name
   - Filter dropdowns:
     * Price range (Under $300K, $300-500K, $500K+)
     * Market status (Bullish/Neutral/Bearish)
     * Alerts only (toggle)
     * Top 10 only (toggle)

3. **City Cards View (Default)**
   - Grid of cards, one per city
   - Each card shows:
     * City name
     * Median price + sparkline
     * Health score gauge
     * Status indicator (🟢🟡🔴)
     * Alert badge if flagged
     * Click to expand details

4. **Top 10 Table View**
   - Sortable table
   - Click column headers to sort
   - Highlight row on hover
   - Click row to see detailed modal

5. **Alerts List View**
   - Shows only flagged cities
   - Grouped by severity (High/Medium/Low)
   - Quick action recommendations

6. **All Cities View**
   - Comprehensive table with all metrics
   - Pagination (20 cities per page)
   - Export to CSV button

### Technical Implementation

```html
<!DOCTYPE html>
<html>
<head>
    <title>[Metro] Market Intelligence Dashboard - [Month Year]</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* Dark theme */
        body { background: #1a1a2e; color: #eee; }
        .card { background: #16213e; border: 1px solid #0f3460; }
        .gauge { /* Custom gauge styling */ }
    </style>
</head>
<body>
    <!-- Metro Overview Panel -->
    <div id="metro-overview" class="sticky top-0 z-50">
        <!-- Health score, key metrics -->
    </div>

    <!-- Tabs -->
    <div id="tabs">
        <button onclick="showView('cards')">City Cards</button>
        <button onclick="showView('top10')">Top 10</button>
        <button onclick="showView('alerts')">Alerts</button>
        <button onclick="showView('all')">All Cities</button>
    </div>

    <!-- Content Area -->
    <div id="content">
        <!-- Dynamic content based on selected view -->
    </div>

    <script>
        // Load city data from JSON
        const cityData = /* INJECT cities_data_[metro]_YYYY-MM.json */;

        // Functions for filtering, sorting, displaying
        function filterCities(criteria) { /* ... */ }
        function showView(viewName) { /* ... */ }
        function showCityDetails(cityName) { /* ... */ }
    </script>
</body>
</html>
```

---

## OUTPUT 3: City Alerts Report (Flagged Cities Only)

**File:** `city_alerts_[METRO]_YYYY-MM.md`

Only includes cities with significant changes or concerns:

```markdown
# [METRO] City Alerts - [Month Year]

**Alert Threshold:** Changes >20% MoM or >30% YoY
**Cities Flagged:** [COUNT] out of [TOTAL]

---

## HIGH SEVERITY ALERTS 🔴

### [City Name]
**Alert Type:** Inventory Surge + Price Decline
**Trigger:** Inventory +XX% MoM, Price -X% MoM

**Current Metrics:**
- Median Price: $XXX,XXX (-X% MoM, -X% YoY)
- Inventory: XXX homes (+XX% MoM)
- Days on Market: XX days (+XX% MoM)
- Homes Sold: XX (-XX% MoM)

**Analysis:**
[What's happening in this specific city and why it matters]

**Recommended Action:**
- **Sellers:** Price X% below current listings, expect XX+ days to sell
- **Buyers:** Strong negotiating position, XX% of listings have price cuts
- **Timeline:** [Expected market conditions for next 30-60 days]

**Historical Context:**
[How this compares to this city's past 12 months]

---

## MEDIUM SEVERITY ALERTS 🟡

[Similar format for medium priority cities]

---

## CITIES TO MONITOR 👀

[Cities approaching alert thresholds or showing early warning signs]

---
```

---

## OUTPUT 4: JSON Data File (Powers the Dashboard)

**File:** `cities_data_[METRO]_YYYY-MM.json`

```json
{
  "meta": {
    "metro_name": "Charlotte-Concord-Gastonia, NC-SC",
    "report_date": "2025-09-30",
    "cities_count": 105,
    "metro_health_score": 65,
    "metro_median_price": 420000,
    "metro_dom": 52,
    "metro_inventory": 12450
  },
  "cities": [
    {
      "name": "Charlotte",
      "state": "NC",
      "median_sale_price": 445000,
      "median_sale_price_mom": 0.02,
      "median_sale_price_yoy": 0.05,
      "homes_sold": 856,
      "inventory": 3245,
      "inventory_mom": 0.15,
      "median_dom": 48,
      "median_dom_mom": 0.10,
      "pending_sales": 420,
      "months_of_supply": 3.8,
      "sold_above_list": 0.32,
      "price_drops": 1240,
      "health_score": 68,
      "status": "NEUTRAL",
      "alert_level": "NONE",
      "sparkline_data": [440000, 442000, 445000],
      "top_10": true,
      "rank": 1
    },
    // ... more cities
  ],
  "alerts": [
    {
      "city": "Matthews",
      "severity": "HIGH",
      "reason": "Inventory surge +35% MoM",
      "recommendation": "Aggressive pricing needed"
    }
  ]
}
```

---

## EXECUTION WORKFLOW

**STEP 1: Run Python Pipeline (Automated)**
```bash
python run_market_analysis.py
```

This automated pipeline will:
1. Extract metros from raw city_market_tracker.tsv000.gz (extract_metros.py)
2. Process filtered TSV files into JSON with 12-month trends (process_market_data.py)
3. Generate enhanced HTML dashboards with interactive charts (generate_dashboards_v2.py)

**STEP 2: Load Generated Data**
- Read `charlotte/2025-09/charlotte_data.json`
- Read `roanoke/2025-09/roanoke_data.json`
- Review generated dashboards to understand what visualizations already exist

**STEP 3: Generate Strategic AI Reports**

Your job is to add the AI analysis layer that the Python scripts cannot provide:

1. **Metro Report** (`metro_report_[metro]_YYYY-MM.md`)
   - Interpret the trends from JSON data
   - Provide market context and strategic insights
   - Identify opportunities and risks
   - Recommend actions for sellers, buyers, investors

2. **City Alerts** (`city_alerts_[metro]_YYYY-MM.md`)
   - Deep dive into flagged cities from top_cities data
   - Explain WHY changes are happening (local factors, trends)
   - Provide tactical recommendations
   - Set expectations for next 30-60 days

**STEP 4: File Organization**
- Save AI reports to `[metro]/YYYY-MM/` folder
- Total output per metro:
  - 2 JSON files (from Python)
  - 2 HTML dashboards (from Python)
  - 2 AI reports (from you)
  - = 6 files per metro (manageable!)

---

## METRIC CALCULATIONS

### Metro-Level Aggregation

Calculate weighted averages based on volume:
- **Metro Median Price** = Weighted by homes_sold per city
- **Metro DOM** = Weighted average across all cities
- **Metro Inventory** = Sum of all city inventories

### Health Score (0-100)

For each city, calculate based on:
1. **Pending Sales Strength** (0-25 pts)
2. **Velocity Health** (0-25 pts)
3. **Inventory Balance** (0-25 pts)
4. **Price Momentum** (0-25 pts)

Interpretation:
- 70-100: BULLISH 🟢
- 40-69: NEUTRAL 🟡
- 0-39: BEARISH 🔴

### Alert Triggers

**High Severity:**
- Any metric >20% MoM change
- Inventory +30% YoY + Price -5% YoY (combo trigger)
- DOM >80 days + increasing

**Medium Severity:**
- Metric 15-20% MoM change
- YoY change >30%
- Months of supply >6 months

---

## SUCCESS CRITERIA

✅ Single comprehensive metro report (not 100+ files!)
✅ Top 10 cities highlighted for quick reference
✅ Alerts identify which cities need attention
✅ Interactive dashboard allows exploration of all cities
✅ JSON data enables programmatic access
✅ Reports are actionable, not overwhelming
✅ Each metro generates only 4 files
✅ Total output: 8 files for both metros (manageable!)
