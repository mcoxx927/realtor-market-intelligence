# Real Estate Data Sources & Automation Guide
## Comprehensive Strategy for Zip Code & Neighborhood Level Analysis

**Created:** October 15, 2025
**Purpose:** Enable more granular market analysis for strategic pricing decisions at the zip code level

---

## EXECUTIVE SUMMARY

**Current State:**
- Metro-level data: Charlotte-Concord-Gastonia & Roanoke (monthly)
- County-level data: 4 counties for Charlotte, county data for Roanoke (monthly)

**Target State:**
- Zip code level data for both markets
- Automated data collection and analysis
- Weekly or daily updates capability
- Neighborhood-level insights for pricing strategy

**Recommended Path:** Multi-source approach combining free public data + MCP automation

---

## CURRENT DATA ASSETS

### What You Already Have

**1. Metro-Level Data (Realtor.com)**
- File: `Realtor New Listings.xlsx`
- Granularity: MSA (Metropolitan Statistical Area)
- Markets: Charlotte (#21), Roanoke (#160)
- 111 months of history (July 2016 - September 2025)

**2. County-Level Data (Realtor.com)**
- File: `RDC_Inventory_Core_Metrics_County_History.xlsx`
- Charlotte Counties: Cabarrus, Gaston, Iredell, Mecklenburg
- Roanoke Counties: Available in ROA sheet
- Same metrics as metro-level but by county

**3. County Hotness Metrics (Realtor.com)**
- File: `RDC_Inventory_Hotness_Metrics_County_History.xlsx`
- Additional demand/velocity indicators by county

### Data Gap Analysis

**Missing Granularity:**
- Zip code level (most critical for pricing strategy)
- Neighborhood level (ideal for micro-market analysis)
- Sub-neighborhood / subdivision level (future consideration)

**Charlotte Market Example:**
- Metro: 1 data point
- County: 4 data points
- Zip Codes: ~50+ data points (TARGET)
- Neighborhoods: ~200+ data points (STRETCH GOAL)

---

## ZIP CODE DATA SOURCES

### Option 1: Redfin Data Center (FREE - RECOMMENDED)

**Overview:**
- Free, downloadable housing market data
- Updated weekly (every Wednesday)
- Zip code level granularity available
- Historical data included

**Access Method:**
```
URL: https://www.redfin.com/news/data-center/

Steps:
1. Visit Redfin Data Center
2. Right-click "Zip Code" data download link
3. Download tsv000.gz file (tab-separated, compressed)
4. Extract and process with Python/Excel
```

**Available Metrics:**
- Median sale price
- Homes sold
- New listings
- Days on market
- Price drops
- Inventory levels
- Year-over-year changes

**Data Format:**
- TSV (tab-separated values), gzipped
- Weekly rolling windows (1, 4, or 12 weeks)
- Updated every Wednesday with prior week data

**Automation Potential:**
- Script can download weekly automatically
- Parse and integrate with existing analysis
- Low cost: FREE

**Pros:**
- Completely free
- Zip code level
- Weekly updates
- Historical data
- Reliable source

**Cons:**
- Manual download (can be automated with script)
- TSV format requires parsing
- Covers major markets only

---

### Option 2: Zillow Research Data (FREE)

**Overview:**
- Comprehensive housing data at multiple geographic levels
- Zip code, neighborhood, city, county, metro, state
- Historical data back to late 1990s
- Updated monthly

**Access Method:**
```
URL: https://www.zillow.com/research/data/

Data Available:
1. Zillow Home Value Index (ZHVI) - by zip code
2. Zillow Observed Rent Index (ZORI) - by zip code
3. Housing inventory metrics
4. Sales data
5. Market temperature indices
```

**Available Metrics:**
- Home values (ZHVI)
- Rent estimates
- Inventory
- Sales volume
- Price cuts
- List to sale ratios

**Data Format:**
- CSV files downloadable directly
- One file per metric
- Long-term historical data

**Automation Potential:**
- Direct CSV download via script
- Can be scheduled monthly
- Free API available (Economic Data API)

**Pros:**
- Free and comprehensive
- Zip code + neighborhood level
- Long historical data
- Multiple metrics
- Direct CSV format

**Cons:**
- Monthly updates only
- Some metrics limited by geography
- Less real-time than Redfin

---

### Option 3: FRED API (FREE)

**Overview:**
- Federal Reserve Economic Data
- Includes Realtor.com Housing Inventory Core Metrics
- Also includes Zillow data indices
- Free API with registration

**Access Method:**
```
URL: https://fred.stlouisfed.org/docs/api/fred/

Registration: Free API key required
API Endpoint: https://api.stlouisfed.org/fred/

Available Data:
- Housing Inventory Core Metrics (62,000+ series)
- Zillow Home Value Index (by metro/state)
- House Price Indexes
- Days on Market
- Active listing counts
```

**Granularity:**
- Primarily MSA (metro) and state level
- Some county-level data available
- Limited zip code level through Zillow ZHVI series

**Automation Potential:**
- Full REST API
- Easy to integrate
- Python library available: `fredapi`
- Can automate monthly pulls

**Pros:**
- Official Federal Reserve data
- Free API access
- Well-documented
- Python/R libraries available
- Reliable and authoritative

**Cons:**
- Limited zip code granularity
- Primarily metro/county level
- Monthly updates only
- Best for macro trends, not micro-markets

**Best Use Case:**
- Economic context for your markets
- Metro-level benchmarking
- Validating other data sources

---

## MCP SERVERS FOR AUTOMATION

### What is MCP?

**Model Context Protocol (MCP)** allows Claude Code and other AI tools to directly access real-time data through standardized server connections. Think of it as a direct pipeline from data sources to your analysis.

### Available Real Estate MCPs

#### 1. Zillow MCP Server (RECOMMENDED)

**Repository:** `github.com/sap156/zillow-mcp-server`

**Features:**
- Real-time property search by location
- Price range filtering
- Property feature search
- Market trends analysis
- Detailed property information
- Built with Python + FastMCP

**How It Works:**
```
Claude Code <-> MCP Server <-> Zillow API <-> Live Data
```

**Setup:**
1. Install MCP server via Claude Code settings
2. Configure with Zillow credentials (if needed)
3. Agent can query directly via natural language

**Example Usage:**
```
"Fetch all active listings in zip code 28203 (Charlotte)
with price range $300k-$500k"

"Get median days on market for Roanoke zip code 24014"

"Compare inventory levels across all Charlotte zip codes"
```

**Automation Potential:**
- Schedule weekly/daily queries
- Auto-generate reports by zip code
- Real-time alerting on market changes

**Cost:** FREE (uses public Zillow data)

---

#### 2. Redfin MCP Server

**Apify MCP Implementation:** Multiple scrapers available

**Features:**
- Property search and listing data
- Agent reviews and ratings
- Market analytics
- Bulk URL processing
- No daily call limits

**Setup:**
1. Create free Apify account
2. Install Redfin MCP server in Claude Code
3. Configure with Apify API token

**Automation Potential:**
- Scrape zip code level data
- Extract property-level details
- Monitor new listings by zip code

**Cost:** FREE tier available (limited), paid plans for scale

---

#### 3. Real Estate Investment MCP Server

**Implementation:** Combined data sources

**Features:**
- SQLite database of real estate data
- Natural language queries
- Investment analysis tools
- Mortgage calculators
- Planned Zillow + Redfin integration

**Best Use Case:**
- Quick ad-hoc queries
- Investment decision support
- Comparative analysis

---

## RECOMMENDED IMPLEMENTATION STRATEGY

### Phase 1: Immediate (Week 1) - FREE

**Goal:** Get zip code data flowing into analysis

**Actions:**
1. **Download Redfin Zip Code Data**
   - Visit Redfin Data Center
   - Download Charlotte zip codes TSV
   - Download Roanoke zip codes TSV
   - Extract and import into Excel/Python

2. **Download Zillow Zip Code Data**
   - Visit Zillow Research
   - Download ZHVI by zip code (Charlotte counties)
   - Download ZHVI by zip code (Roanoke)
   - Download inventory metrics by zip code

3. **Modify Existing Agent**
   - Update Real-Estate-Market-Intelligence-Agent
   - Add zip code analysis capability
   - Generate reports by zip code instead of just metro/county

**Expected Outcome:**
- Zip code level dashboards for Charlotte (~50 zips)
- Zip code level dashboards for Roanoke (~10-15 zips)
- Weekly manual updates (15 minutes/week)

**Cost:** $0

---

### Phase 2: Automation (Week 2-3) - FREE

**Goal:** Automate data collection

**Actions:**
1. **Install Zillow MCP Server**
   ```bash
   # In Claude Code settings, add MCP server
   npm install -g zillow-mcp-server
   ```

2. **Create Data Collection Scripts**
   - Python script to download Redfin data weekly
   - Python script to download Zillow data monthly
   - Schedule with Windows Task Scheduler

3. **Update Agent Workflows**
   - Agent automatically pulls latest zip code data
   - Processes and generates reports
   - No manual intervention needed

**Example Automation Script:**
```python
import requests
import pandas as pd
from datetime import datetime

def download_redfin_zipcode_data():
    # Download latest Redfin zip code data
    url = "https://redfin-public-data.s3.amazonaws.com/..."
    df = pd.read_csv(url, compression='gzip', sep='\t')

    # Filter for Charlotte and Roanoke zip codes
    charlotte_zips = df[df['region_name'].isin(charlotte_zip_list)]
    roanoke_zips = df[df['region_name'].isin(roanoke_zip_list)]

    # Save to processed folder
    charlotte_zips.to_csv(f'charlotte/data/zipcode_{datetime.now():%Y%m}.csv')
    roanoke_zips.to_csv(f'roanoke/data/zipcode_{datetime.now():%Y%m}.csv')

    return True

# Schedule to run every Wednesday at 9 AM
```

**Expected Outcome:**
- Fully automated weekly updates
- Agent runs automatically, generates reports
- Email/notification when new reports ready

**Cost:** $0

---

### Phase 3: Advanced Integration (Week 4+) - FREE TO LOW COST

**Goal:** Real-time insights and predictive analytics

**Actions:**
1. **FRED API Integration**
   - Pull macro economic indicators
   - Correlate with local market data
   - Add economic context to reports

2. **Property-Level Data**
   - Use MCP to pull individual property data
   - Build comps database by zip code
   - Enable "pricing assistant" for specific addresses

3. **Neighborhood Clustering**
   - Use ML to cluster zip codes into micro-markets
   - Identify leading indicators across neighborhoods
   - Predictive pricing models

**Expected Outcome:**
- Real-time market intelligence
- Predictive pricing recommendations
- Micro-market trend identification
- Competitive advantage in pricing strategy

**Cost:** $0-50/month (if using paid API tiers for scale)

---

## RECOMMENDED DATA ARCHITECTURE

### Folder Structure

```
realtor monthly data analysis/
├── data/
│   ├── metro/              # Existing metro-level data
│   ├── county/             # Existing county-level data
│   └── zipcode/            # NEW: Zip code level data
│       ├── charlotte/
│       │   ├── redfin/     # Redfin weekly data
│       │   ├── zillow/     # Zillow monthly data
│       │   └── processed/  # Cleaned & merged data
│       └── roanoke/
│           ├── redfin/
│           ├── zillow/
│           └── processed/
│
├── charlotte/
│   ├── metro/
│   │   └── 2025-09/        # Existing metro reports
│   ├── county/             # NEW: County-level reports
│   │   ├── mecklenburg/
│   │   ├── cabarrus/
│   │   ├── gaston/
│   │   └── iredell/
│   └── zipcode/            # NEW: Zip code reports
│       ├── 28203/          # Example: South End Charlotte
│       ├── 28204/          # Example: Dilworth
│       └── ...
│
├── roanoke/
│   ├── metro/
│   ├── county/
│   └── zipcode/
│
└── scripts/
    ├── download_redfin.py
    ├── download_zillow.py
    ├── process_zipcode_data.py
    └── scheduled_report_generator.py
```

---

## COST-BENEFIT ANALYSIS

### Current Approach (Metro-Level Only)

**Pros:**
- Simple, single data point per market
- Easy to track trends

**Cons:**
- No granularity for pricing decisions
- Can't identify high-performing neighborhoods
- Slow to react to micro-market shifts
- Competitive disadvantage

**Business Impact:**
- Pricing decisions lag market by 30-60 days
- Miss opportunities in hot zip codes
- Overprice in cooling zip codes
- Revenue impact: Unknown but likely significant

---

### Recommended Approach (Zip Code + Automation)

**Implementation Costs:**
- Phase 1 (Manual): $0, 4 hours setup
- Phase 2 (Automation): $0, 8 hours setup
- Phase 3 (Advanced): $0-50/month, 16 hours setup

**Total First Month:** $0-50, 28 hours investment

**Ongoing Costs:**
- Maintenance: 2 hours/month
- Data costs: $0-50/month
- No additional software needed

**Benefits:**
- **Pricing Accuracy:** Know exact market conditions by zip code
- **Speed to Market:** Weekly updates vs monthly
- **Competitive Intel:** See which neighborhoods are heating/cooling
- **Strategic Planning:** Data-driven territory decisions
- **Team Efficiency:** Automated reports = less manual work

**Business Impact (Estimated):**
- 10-20% faster pricing decisions
- 5-15% more accurate pricing (fewer price adjustments)
- 2-3 hours/week saved on manual data gathering
- Better territory allocation for team

**ROI:** Immediate (free data) to very high (paid options)

---

## SPECIFIC ZIP CODES TO PRIORITIZE

### Charlotte Metro (50+ zip codes)

**High Priority Zips (Affluent/High Volume):**
- 28203 (South End) - High rise condos
- 28204 (Dilworth) - Historic, walkable
- 28207 (Myers Park) - Luxury
- 28209 (South Park) - Affluent suburban
- 28211 (South Charlotte) - Family homes
- 28226 (Ballantyne) - New construction
- 28277 (South Charlotte) - Growing market

**Medium Priority:**
- 28105 (Matthews)
- 28104 (Pineville)
- 28031 (Cornelius)
- 28078 (Huntersville)

**Total Charlotte Zips to Track:** ~30-40 for comprehensive coverage

---

### Roanoke Metro (10-15 zip codes)

**High Priority Zips:**
- 24012 (South Roanoke) - Historic
- 24014 (Southwest) - Residential
- 24018 (Cave Spring) - Affluent
- 24019 (North Roanoke)
- 24153 (Salem) - Adjacent city

**Total Roanoke Zips to Track:** ~10-12 for full coverage

---

## IMPLEMENTATION CHECKLIST

### Week 1: Data Collection
- [ ] Create data/zipcode folder structure
- [ ] Download Redfin zip code data for Charlotte
- [ ] Download Redfin zip code data for Roanoke
- [ ] Download Zillow ZHVI for target zip codes
- [ ] Identify priority zip codes list (30 Charlotte, 10 Roanoke)
- [ ] Import data into Excel/Python for validation

### Week 2: Agent Modification
- [ ] Update Real-Estate-Market-Intelligence-Agent for zip code analysis
- [ ] Test agent with 1-2 zip codes
- [ ] Generate sample zip code dashboard
- [ ] Review output with team
- [ ] Iterate on report format

### Week 3: Automation
- [ ] Install Zillow MCP server
- [ ] Create Python download scripts
- [ ] Schedule weekly automation (Windows Task Scheduler)
- [ ] Test full workflow end-to-end
- [ ] Document process for team

### Week 4: Scale & Optimize
- [ ] Generate reports for all priority zip codes
- [ ] Create master dashboard comparing all zips
- [ ] Set up alerting for significant changes
- [ ] Train team on new reports
- [ ] Gather feedback and iterate

---

## GETTING STARTED TODAY

### Immediate Action (30 minutes)

1. **Visit Redfin Data Center**
   ```
   https://www.redfin.com/news/data-center/
   ```
   - Click "Zip Code" data
   - Download latest file
   - Extract to data/zipcode/charlotte/redfin/

2. **Visit Zillow Research**
   ```
   https://www.zillow.com/research/data/
   ```
   - Download "ZHVI All Homes (SFR, Condo/Co-op) Time Series, Zip"
   - Filter for North Carolina and Virginia
   - Save to data/zipcode/zillow/

3. **Test with Agent**
   ```
   @agent-Real-Estate-Market-Intelligence-Agent
   Analyze zip code 28203 (Charlotte South End) using the
   Redfin and Zillow data I just downloaded
   ```

---

## ALTERNATIVE: PAID PREMIUM OPTIONS

If budget allows for paid data:

### SimplyRETS API
- Cost: $99-299/month
- MLS data access (requires MLS membership)
- Property-level detail
- Real-time updates

### ATTOM Data Solutions
- Cost: Custom pricing (typically $500+/month)
- Comprehensive property data
- Tax records, ownership history
- Neighborhood analytics

### Rental Analytics (if applicable)
- RentCast API: Zip code rental trends
- Free tier: 500 requests/month
- Paid: $49-199/month

**Recommendation:** Start with free sources, upgrade if ROI proven

---

## QUESTIONS & NEXT STEPS

**Questions to Consider:**
1. Which zip codes are most important for your business?
2. How frequently do pricing decisions get made? (weekly? daily?)
3. Who on the team will use this data?
4. What's the decision-making process that this data informs?

**Let's Start:**
I can help you:
1. Download and process the first batch of zip code data
2. Modify the agent to analyze zip code level data
3. Generate sample zip code dashboards
4. Set up automation scripts

**Which would you like to tackle first?**

---

## APPENDIX: Technical Resources

### Python Libraries for Real Estate Data
```python
# FRED API
pip install fredapi

# Zillow data processing
pip install pandas numpy openpyxl

# Web scraping (if needed)
pip install requests beautifulsoup4

# Data visualization
pip install matplotlib plotly
```

### Useful API Documentation
- FRED API: https://fred.stlouisfed.org/docs/api/fred/
- Zillow Research: https://www.zillow.com/research/data/
- Redfin Data: https://www.redfin.com/news/data-center/

### MCP Server Repositories
- Zillow MCP: https://github.com/sap156/zillow-mcp-server
- Real Estate MCP: https://glama.ai/mcp/servers/@klappe-pm/Real-Estate-MCP

---

*Document Version: 1.0*
*Last Updated: October 15, 2025*
*Contact: Generated by Claude Code*
