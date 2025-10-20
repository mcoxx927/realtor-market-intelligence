"""
Enhanced Dashboard Generator for Redfin City-Level Data
Reads charlotte_data.json and roanoke_data.json
Generates interactive HTML dashboards with historical trends and city comparison
"""

import json
from pathlib import Path

def generate_enhanced_dashboard(data_file: str, output_file: str):
    """Generate enhanced HTML dashboard with metro trends + city comparison"""

    # Read data
    with open(data_file, 'r') as f:
        data = json.load(f)

    metro = data['metro']
    period = data['period']
    metro_trends = data['metro_trends']  # 12-month default
    top_cities = data['top_cities']
    city_trends = data['city_trends']  # Top 5 cities, 12 months
    full_metro_trends = data['full_metro_trends']  # ALL historical data
    full_city_trends = data['full_city_trends']  # ALL cities, ALL history
    available_cities = data['available_cities']  # List of all city names
    period_index_full = data.get('period_index_full', [t['period'] for t in full_metro_trends])
    period_index_12m = data.get('period_index_12m', [t['period'] for t in metro_trends])
    period_index_by_city = data.get('period_index_by_city', {})

    # Current month stats
    current = metro_trends[-1]

    # Format period labels
    labels = [t['period'] for t in metro_trends]
    labels_formatted = []
    for label in labels:
        year, month = label.split('-')
        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        labels_formatted.append(f"{month_names[int(month)]} '{year[2:]}")

    # Extract metro trends
    inventory_data = [t['inventory'] for t in metro_trends]
    new_listings_data = [t['new_listings'] for t in metro_trends]
    pending_data = [t['pending_sales'] for t in metro_trends]
    price_drops_data = [t['price_drops'] for t in metro_trends]
    dom_data = [t['median_dom'] for t in metro_trends]
    pending_ratio_data = [t['pending_ratio'] if t['pending_ratio'] else 0 for t in metro_trends]
    homes_sold_data = [t['homes_sold'] for t in metro_trends]
    median_price_data = [t['median_sale_price'] for t in metro_trends]

    # Calculate flipper metrics (current month)
    months_supply = round(current['inventory'] / current['homes_sold'], 1) if current['homes_sold'] > 0 else 0
    absorption_rate = round((current['homes_sold'] / current['inventory']) * 100, 1) if current['inventory'] > 0 else 0
    supply_demand_ratio = round(current['new_listings'] / current['homes_sold'], 2) if current['homes_sold'] > 0 else 0

    # Determine market type
    if months_supply < 5:
        market_type = "SELLER'S MARKET"
        market_type_color = "red"
    elif months_supply > 6:
        market_type = "BUYER'S MARKET"
        market_type_color = "green"
    else:
        market_type = "BALANCED"
        market_type_color = "yellow"

    # Calculate YoY changes (current vs 12 months ago)
    if len(metro_trends) >= 12:
        prev_year = metro_trends[0]
        dom_yoy = round(((current['median_dom'] - prev_year['median_dom']) / prev_year['median_dom']) * 100) if prev_year['median_dom'] > 0 else 0
        inventory_yoy = round(((current['inventory'] - prev_year['inventory']) / prev_year['inventory']) * 100) if prev_year['inventory'] > 0 else 0
    else:
        dom_yoy = 0
        inventory_yoy = 0

    # Calculate buy/sell signals for cities
    buy_cities = []
    hold_cities = []
    sell_cities = []

    for city in top_cities:
        city_months_supply = round(city['inventory'] / city['sales'], 1) if city['sales'] > 0 else 0
        city['months_supply'] = city_months_supply
        city['absorption_rate'] = round((city['sales'] / city['inventory']) * 100, 1) if city['inventory'] > 0 else 0

        # Determine signal
        if city_months_supply > 5:
            city['signal'] = 'BUY'
            city['signal_color'] = 'green'
            if len(buy_cities) < 3:
                buy_cities.append(city)
        elif city_months_supply < 3:
            city['signal'] = 'SELL'
            city['signal_color'] = 'red'
            if len(sell_cities) < 3:
                sell_cities.append(city)
        else:
            city['signal'] = 'HOLD'
            city['signal_color'] = 'yellow'
            if len(hold_cities) < 3:
                hold_cities.append(city)

    # City selector options (all available cities sorted by latest sales)
    def latest_sales(city_name: str) -> int:
        series = full_city_trends.get(city_name) or city_trends.get(city_name) or []
        if not series:
            return 0
        return series[-1].get('homes_sold') or 0

    city_names = sorted(available_cities, key=latest_sales, reverse=True)

    # Build city dropdown options
    city_options = '\n'.join([f'<option value="{city}">{city}</option>' for city in city_names])
    city_names_json = json.dumps(city_names)

    # Pre-build buy/sell/hold city lists HTML
    buy_cities_html = '\n'.join([f'                        <div>• {city["name"]} - {city["months_supply"]}mo, DOM {city["dom"]}</div>' for city in buy_cities[:3]])
    hold_cities_html = '\n'.join([f'                        <div>• {city["name"]} - {city["months_supply"]}mo, DOM {city["dom"]}</div>' for city in hold_cities[:3]])
    sell_cities_html = '\n'.join([f'                        <div>• {city["name"]} - {city["months_supply"]}mo, DOM {city["dom"]}</div>' for city in sell_cities[:3]])

    # Prepare JSON data for JavaScript (12-month default view only)
    labels_json = json.dumps(labels_formatted)
    periods_json = json.dumps(labels)
    inventory_json = json.dumps(inventory_data)
    new_listings_json = json.dumps(new_listings_data)
    pending_json = json.dumps(pending_data)
    price_drops_json = json.dumps(price_drops_data)
    dom_json = json.dumps(dom_data)
    pending_ratio_json = json.dumps(pending_ratio_data)
    homes_sold_json = json.dumps(homes_sold_data)
    median_price_json = json.dumps(median_price_data)
    city_trends_json = json.dumps(city_trends)
    full_metro_trends_json = json.dumps(full_metro_trends)
    full_city_trends_json = json.dumps(full_city_trends)
    available_cities_json = json.dumps(available_cities)
    period_json = json.dumps(period)
    period_index_full_json = json.dumps(period_index_full)
    period_index_12m_json = json.dumps(period_index_12m)
    period_index_by_city_json = json.dumps(period_index_by_city)

    # Derived metric arrays for tooltips and fallbacks
    inventory_mom_json = json.dumps([t.get('inventory_mom') for t in metro_trends])
    inventory_yoy_json = json.dumps([t.get('inventory_yoy') for t in metro_trends])
    new_listings_mom_json = json.dumps([t.get('new_listings_mom') for t in metro_trends])
    new_listings_yoy_json = json.dumps([t.get('new_listings_yoy') for t in metro_trends])
    pending_sales_mom_json = json.dumps([t.get('pending_sales_mom') for t in metro_trends])
    pending_sales_yoy_json = json.dumps([t.get('pending_sales_yoy') for t in metro_trends])
    homes_sold_mom_json = json.dumps([t.get('homes_sold_mom') for t in metro_trends])
    homes_sold_yoy_json = json.dumps([t.get('homes_sold_yoy') for t in metro_trends])
    price_drops_mom_json = json.dumps([t.get('price_drops_mom') for t in metro_trends])
    price_drops_yoy_json = json.dumps([t.get('price_drops_yoy') for t in metro_trends])
    dom_mom_json = json.dumps([t.get('median_dom_mom') for t in metro_trends])
    dom_yoy_json = json.dumps([t.get('median_dom_yoy') for t in metro_trends])
    price_mom_json = json.dumps([t.get('median_sale_price_mom') for t in metro_trends])
    price_yoy_json = json.dumps([t.get('median_sale_price_yoy') for t in metro_trends])
    pending_ratio_mom_json = json.dumps([t.get('pending_ratio_mom') for t in metro_trends])
    pending_ratio_yoy_json = json.dumps([t.get('pending_ratio_yoy') for t in metro_trends])
    months_supply_series_json = json.dumps([t.get('months_of_supply') for t in metro_trends])
    absorption_rate_json = json.dumps([t.get('absorption_rate') for t in metro_trends])
    supply_demand_series_json = json.dumps([t.get('supply_demand_ratio') for t in metro_trends])

    # Pre-build YoY change strings
    inventory_yoy_str = f"up {inventory_yoy}%" if inventory_yoy > 0 else f"down {abs(inventory_yoy)}%"
    dom_yoy_str = f"up {dom_yoy}%" if dom_yoy > 0 else f"down {abs(dom_yoy)}%"
    market_type_lower = market_type.lower()

    # Pre-build risk alert message
    if months_supply > 6:
        risk_alert = "Market softening - expect 5-10% price corrections in weaker submarkets."
    elif months_supply < 4:
        risk_alert = "Low inventory - watch for over-competition on acquisitions."
    else:
        risk_alert = "Stable conditions - normal market dynamics."

    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metro} Market Intelligence Dashboard - {period}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        .card {{
            background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}
        .selector {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
        }}
        .selector:hover {{
            background: rgba(255, 255, 255, 0.15);
        }}
        /* Ensure select dropdown options remain readable across platforms */
        select.selector option {{
            color: #111827; /* tailwind gray-900 */
            background-color: #ffffff;
        }}
    </style>
</head>
<body class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto space-y-6">

        <!-- Header -->
        <div class="card p-8 text-white">
            <h1 class="text-4xl font-bold mb-2">{metro} Market Intelligence</h1>
            <p class="text-xl text-gray-300">{period} Analysis - {data['current_stats']['total_cities']} Cities</p>
        </div>

        <!-- Date Range Selector -->
        <div class="card p-6 text-white">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h3 class="text-lg font-bold mb-1">Date Range</h3>
                    <p class="text-sm text-gray-400" id="dateRangeDisplay">Last 12 Months (Default)</p>
                </div>
                <div class="flex flex-wrap gap-2 items-center">
                    <button data-range="6m" onclick="setDateRange('6m', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">Last 6 Months</button>
                    <button data-range="12m" onclick="setDateRange('12m', this)" class="px-4 py-2 bg-blue-500/40 border-2 border-blue-500 rounded-lg text-sm font-bold">Last 12 Months</button>
                    <button data-range="ytd" onclick="setDateRange('ytd', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">YTD 2025</button>
                    <button data-range="2y" onclick="setDateRange('2y', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">Last 2 Years</button>
                    <button data-range="5y" onclick="setDateRange('5y', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">Last 5 Years</button>
                    <button data-range="all" onclick="setDateRange('all', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">All Time</button>
                    <button id="btnResetState" class="ml-2 px-3 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-xs" aria-label="Reset dashboard selections">Reset</button>
                </div>
            </div>
        </div>

        <!-- Metro Stats Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="card p-6 text-white">
                <div class="text-sm text-gray-400 mb-2">Total Sales</div>
                <div class="text-3xl font-bold">{current['homes_sold']:,}</div>
            </div>
            <div class="card p-6 text-white">
                <div class="text-sm text-gray-400 mb-2">Median Price</div>
                <div class="text-3xl font-bold">${current['median_sale_price']:,}</div>
            </div>
            <div class="card p-6 text-white">
                <div class="text-sm text-gray-400 mb-2">Days on Market</div>
                <div class="text-3xl font-bold">{current['median_dom']}</div>
            </div>
            <div class="card p-6 text-white">
                <div class="text-sm text-gray-400 mb-2">Active Inventory</div>
                <div class="text-3xl font-bold">{current['inventory']:,}</div>
            </div>
        </div>

        <!-- Market Health Dashboard for Flippers -->
        <div class="card p-6 text-white">
            <h2 class="text-2xl font-bold mb-4">Market Health Dashboard - House Flipper Intelligence</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <!-- Market Type Gauge -->
                <div class="p-4 bg-{market_type_color}-500/20 border border-{market_type_color}-500/50 rounded-lg">
                    <div class="text-sm text-gray-400 mb-2">Market Type</div>
                    <div class="text-xl font-bold text-{market_type_color}-400">{market_type}</div>
                    <div class="text-xs mt-2">&lt;5mo: Seller's | 5-6mo: Balanced | &gt;6mo: Buyer's</div>
                </div>
                <!-- Months of Supply -->
                <div class="p-4 bg-blue-500/20 border border-blue-500/50 rounded-lg">
                    <div class="text-sm text-gray-400 mb-2">Months of Supply</div>
                    <div class="text-3xl font-bold text-blue-400">{months_supply}</div>
                    <div class="text-xs mt-2">Inventory / Sales Rate</div>
                </div>
                <!-- Absorption Rate -->
                <div class="p-4 bg-purple-500/20 border border-purple-500/50 rounded-lg">
                    <div class="text-sm text-gray-400 mb-2">Absorption Rate</div>
                    <div class="text-3xl font-bold text-purple-400">{absorption_rate}%</div>
                    <div class="text-xs mt-2">Sales / Inventory</div>
                </div>
                <!-- Market Trend -->
                <div class="p-4 bg-orange-500/20 border border-orange-500/50 rounded-lg">
                    <div class="text-sm text-gray-400 mb-2">Market Trend (YoY)</div>
                    <div class="text-lg font-bold text-orange-400">DOM {dom_yoy:+d}%</div>
                    <div class="text-xs mt-2">Inventory {inventory_yoy:+d}%</div>
                </div>
            </div>

            <!-- Buy/Sell Signals Summary -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Buy Opportunities -->
                <div class="p-4 bg-green-500/10 border-l-4 border-green-500 rounded">
                    <div class="font-bold text-green-400 mb-2">BUY OPPORTUNITIES ({len(buy_cities)})</div>
                    <div class="text-sm space-y-1">
{buy_cities_html}
                    </div>
                </div>
                <!-- Hold Zones -->
                <div class="p-4 bg-yellow-500/10 border-l-4 border-yellow-500 rounded">
                    <div class="font-bold text-yellow-400 mb-2">HOLD ZONES ({len(hold_cities)})</div>
                    <div class="text-sm space-y-1">
{hold_cities_html}
                    </div>
                </div>
                <!-- Sell Fast -->
                <div class="p-4 bg-red-500/10 border-l-4 border-red-500 rounded">
                    <div class="font-bold text-red-400 mb-2">SELL FAST ({len(sell_cities)})</div>
                    <div class="text-sm space-y-1">
{sell_cities_html}
                    </div>
                </div>
            </div>
        </div>

        <!-- Inventory Dynamics with Dropdown -->
        <div class="card p-6 text-white">
            <div class="flex flex-col gap-4 mb-4">
                <div class="flex justify-between items-center">
                    <h2 class="text-2xl font-bold" id="inventoryChartTitle">Metro Inventory Dynamics (Last 12 Months)</h2>
                    <div class="flex gap-2">
                        <select id="inventoryMetric" class="selector">
                            <option value="all">All Metrics</option>
                            <option value="inventory">Active Listings Only</option>
                            <option value="new_listings">New Listings Only</option>
                            <option value="pending">Pending Sales Only</option>
                        </select>
                        <button onclick="downloadChartImage('inventoryChart', 'inventory_dynamics')" class="px-3 py-2 bg-green-500/20 hover:bg-green-500/40 border border-green-500/50 rounded-lg transition text-sm">
                            <span>Download PNG</span>
                        </button>
                        <button onclick="exportChartCSV('inventoryChart', 'inventory_dynamics')" class="px-3 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm">
                            <span>Download CSV</span>
                        </button>
                    </div>
                </div>
                <div class="flex flex-wrap gap-4 text-sm">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="showMA3" class="w-4 h-4 cursor-pointer" onchange="toggleMovingAverages()">
                        <span>3-Month MA</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="showMA6" class="w-4 h-4 cursor-pointer" onchange="toggleMovingAverages()">
                        <span>6-Month MA</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="showMA12" class="w-4 h-4 cursor-pointer" onchange="toggleMovingAverages()">
                        <span>12-Month MA</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="showTrendLine" class="w-4 h-4 cursor-pointer" onchange="toggleMovingAverages()">
                        <span>Trend Line</span>
                    </label>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="inventoryChart"></canvas>
            </div>
        </div>

        <!-- Price Reductions Chart -->
        <div class="card p-6 text-white">
            <h2 class="text-2xl font-bold mb-4" id="priceDropsChartTitle">Price Reductions (Last 12 Months)</h2>
            <div class="chart-container">
                <canvas id="priceDropsChart"></canvas>
            </div>
        </div>

        <!-- Supply vs Demand Analysis -->
        <div class="card p-6 text-white">
            <h2 class="text-2xl font-bold mb-4" id="supplyDemandChartTitle">Supply vs Demand Balance (Last 12 Months)</h2>
            <div class="mb-4 p-4 bg-blue-500/10 border-l-4 border-blue-500 rounded">
                <div class="text-sm">
                    <strong>Flipper Insight:</strong> When New Listings (supply) exceeds Homes Sold (demand), expect downward price pressure.
                    Current ratio: {supply_demand_ratio} ({"supply outpacing demand" if supply_demand_ratio > 1 else "demand outpacing supply"}).
                </div>
            </div>
            <div class="chart-container">
                <canvas id="supplyDemandChart"></canvas>
            </div>
        </div>

        <!-- Combined DOM + Pending Ratio -->
        <div class="card p-6 text-white">
            <h2 class="text-2xl font-bold mb-4" id="domPendingChartTitle">Days on Market & Pending Ratio (Last 12 Months)</h2>
            <div class="chart-container">
                <canvas id="domPendingChart"></canvas>
            </div>
        </div>

        <!-- City Historical Trends -->
        <div class="card p-6 text-white">
            <div class="flex flex-col gap-4 mb-4">
                <div class="flex flex-wrap gap-3 items-center justify-between">
                    <div>
                        <h2 class="text-2xl font-bold">City Historical Trends</h2>
                        <p class="text-sm text-gray-400">Ordered by latest monthly sales. Compare inventory, listings, and absorption signals.</p>
                    </div>
                    <div class="flex flex-wrap gap-2 items-center">
                        <label class="text-sm" for="citySelector">City</label>
                        <select id="citySelector" class="selector" aria-label="Select city">
                            {city_options}
                        </select>
                        <label class="text-sm" for="cityMetricMode">Metric</label>
                        <select id="cityMetricMode" class="selector" aria-label="Select city metric view">
                            <option value="all">All Metrics</option>
                            <option value="inventory">Inventory</option>
                            <option value="new_listings">New Listings</option>
                            <option value="pending_sales">Pending Sales</option>
                            <option value="homes_sold">Homes Sold</option>
                            <option value="median_sale_price">Median Price</option>
                            <option value="median_dom">Days on Market</option>
                        </select>
                    </div>
                </div>
                <div class="flex flex-wrap gap-4 text-sm" id="cityChartToggles">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="cityShowMA3" class="w-4 h-4 cursor-pointer">
                        <span>3-Month MA</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="cityShowMA6" class="w-4 h-4 cursor-pointer">
                        <span>6-Month MA</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="cityShowMA12" class="w-4 h-4 cursor-pointer">
                        <span>12-Month MA</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" id="cityShowTrend" class="w-4 h-4 cursor-pointer">
                        <span>Trend Line</span>
                    </label>
                </div>
                <div class="flex flex-wrap gap-2 text-xs">
                    <span class="text-gray-400 uppercase tracking-wide">Range:</span>
                    <div class="flex gap-2">
                        <button data-city-range="12m" class="city-range-button px-3 py-1 bg-white/10 border border-white/20 rounded">12m</button>
                        <button data-city-range="24m" class="city-range-button px-3 py-1 bg-white/10 border border-white/20 rounded">24m</button>
                        <button data-city-range="60m" class="city-range-button px-3 py-1 bg-white/10 border border-white/20 rounded">5y</button>
                        <button data-city-range="all" class="city-range-button px-3 py-1 bg-white/10 border border-white/20 rounded">All</button>
                    </div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="cityChart"></canvas>
            </div>
        </div>

        <!-- Multi-City Comparison (New Feature) -->
        <div class="card p-6 text-white">
            <div class="mb-4 flex justify-between items-start">
                <div>
                    <h2 class="text-2xl font-bold mb-2">Multi-City Comparison Tool</h2>
                    <p class="text-sm text-gray-400">Select multiple cities to compare side-by-side. All {len(available_cities)} cities available.</p>
                </div>
                <div class="flex gap-2">
                    <button onclick="downloadChartImage('multiCityChart', 'multi_city_comparison')" class="px-3 py-2 bg-green-500/20 hover:bg-green-500/40 border border-green-500/50 rounded-lg transition text-sm">
                        <span>Download PNG</span>
                    </button>
                    <button onclick="exportChartCSV('multiCityChart', 'multi_city_comparison')" class="px-3 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm">
                        <span>Download CSV</span>
                    </button>
                </div>
            </div>
            <div class="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Search & Select Cities</label>
                    <input type="text" id="citySearch" placeholder="Search cities..." class="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 mb-2">
                    <div class="bg-white/5 border border-white/20 rounded-lg max-h-48 overflow-y-auto p-2" id="cityCheckboxList" role="listbox" aria-label="Select cities for comparison">
                        <!-- Checkboxes will be generated by JavaScript -->
                    </div>
                    <div class="flex flex-wrap gap-2 mt-2">
                        <button id="btnTopSales" class="px-3 py-2 bg-white/10 border border-white/20 rounded text-sm hover:bg-white/20" aria-label="Select top five cities by sales volume">Select Top 5 by Sales</button>
                        <button id="btnTopSupply" class="px-3 py-2 bg-white/10 border border-white/20 rounded text-sm hover:bg-white/20" aria-label="Select top five cities by months of supply">Select Top 5 by MoS</button>
                        <button id="btnClearSel" class="px-3 py-2 bg-white/10 border border-white/20 rounded text-sm hover:bg-white/20" aria-label="Clear selected cities">Clear</button>
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Metric to Compare</label>
                    <select id="multiCityMetric" class="selector w-full mb-4">
                        <option value="inventory">Inventory</option>
                        <option value="sales">Homes Sold</option>
                        <option value="dom">Days on Market</option>
                        <option value="price">Median Price</option>
                    </select>
                    <div>
                        <div class="text-sm font-medium mb-2">Selected Cities (<span id="selectedCount">0</span>)</div>
                        <div id="selectedCitiesList" class="text-sm text-gray-400 min-h-[100px]">
                            No cities selected. Use checkboxes to select cities.
                        </div>
                    </div>
                </div>
            </div>
            <div class="flex flex-wrap gap-4 text-sm mb-4">
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" id="multiCityMA3" class="w-4 h-4 cursor-pointer" onchange="updateMultiCityChart()">
                    <span>3-Month MA</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" id="multiCityMA6" class="w-4 h-4 cursor-pointer" onchange="updateMultiCityChart()">
                    <span>6-Month MA</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" id="multiCityMA12" class="w-4 h-4 cursor-pointer" onchange="updateMultiCityChart()">
                    <span>12-Month MA</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" id="multiCityTrend" class="w-4 h-4 cursor-pointer" onchange="updateMultiCityChart()">
                    <span>Trend Lines</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" id="multiCityMetro" class="w-4 h-4 cursor-pointer">
                    <span>Metro Benchmark</span>
                </label>
            </div>
            <div class="chart-container" style="height: 400px;">
                <canvas id="multiCityChart"></canvas>
            </div>
        </div>

        <!-- Top Cities Table -->
        <div class="card p-6 text-white">
            <h2 class="text-2xl font-bold mb-4">Top 10 Cities by Sales Volume - Flipper Analysis</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="border-b border-gray-600">
                        <tr class="text-left">
                            <th class="pb-3">City</th>
                            <th class="pb-3">Sales</th>
                            <th class="pb-3">Median Price</th>
                            <th class="pb-3">Price YoY</th>
                            <th class="pb-3">DOM</th>
                            <th class="pb-3">Mo Supply</th>
                            <th class="pb-3">Absorption%</th>
                            <th class="pb-3">Signal</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    for city in top_cities:
        price_yoy_class = 'text-green-400' if city['price_yoy'] and city['price_yoy'] > 0 else 'text-red-400' if city['price_yoy'] and city['price_yoy'] < 0 else 'text-gray-400'
        price_yoy_display = f"{city['price_yoy']*100:.1f}%" if city['price_yoy'] else 'N/A'

        # Signal badge styling
        if city['signal'] == 'BUY':
            signal_badge = f'<span class="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-bold">BUY</span>'
        elif city['signal'] == 'SELL':
            signal_badge = f'<span class="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs font-bold">SELL</span>'
        else:
            signal_badge = f'<span class="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs font-bold">HOLD</span>'

        html += f'''                        <tr class="border-b border-gray-700">
                            <td class="py-3 font-medium">{city['name']}</td>
                            <td class="py-3">{city['sales']}</td>
                            <td class="py-3">${city['price']:,}</td>
                            <td class="py-3 {price_yoy_class}">{price_yoy_display}</td>
                            <td class="py-3">{city['dom']}</td>
                            <td class="py-3 font-bold">{city['months_supply']}</td>
                            <td class="py-3">{city['absorption_rate']}%</td>
                            <td class="py-3">{signal_badge}</td>
                        </tr>
'''

    html += f'''                    </tbody>
                </table>
            </div>
        </div>

        <!-- AI-Powered Flipper Insights -->
        <div class="card p-6 text-white">
            <h2 class="text-2xl font-bold mb-4">AI-Powered Flipper Insights - {period}</h2>
            <div class="grid md:grid-cols-2 gap-6 mb-6">
                <!-- Buy Opportunities -->
                <div class="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <h3 class="text-xl font-bold text-green-400 mb-3">Top Buy Opportunities</h3>
                    <div class="space-y-3">
'''

    # Generate buy opportunities
    for i, city in enumerate(buy_cities[:3], 1):
        dom_trend = "weakening demand" if dom_yoy > 10 else "stable demand"
        price_trend = "motivated sellers" if city['price_yoy'] and city['price_yoy'] < 0 else "holding firm"

        html += f'''                        <div class="p-3 bg-black/20 rounded">
                            <div class="font-bold">{i}. {city['name']} - STRONG BUY</div>
                            <div class="text-sm mt-1">• {city['months_supply']} months supply (buyer's market)</div>
                            <div class="text-sm">• DOM {city['dom']} days</div>
                            <div class="text-sm">• Prices {f"{city['price_yoy']*100:.1f}%" if city['price_yoy'] else "stable"} YoY ({price_trend})</div>
                            <div class="text-sm text-green-400 mt-2">Strategy: Negotiate 10-15% below list, quick close</div>
                        </div>
'''

    html += '''                    </div>
                </div>
                <!-- Sell Fast Zones -->
                <div class="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <h3 class="text-xl font-bold text-red-400 mb-3">Sell Fast Zones</h3>
                    <div class="space-y-3">
'''

    # Generate sell fast zones
    for i, city in enumerate(sell_cities[:3], 1):
        html += f'''                        <div class="p-3 bg-black/20 rounded">
                            <div class="font-bold">{i}. {city['name']} - SELL NOW</div>
                            <div class="text-sm mt-1">• {city['months_supply']} months supply (seller's market)</div>
                            <div class="text-sm">• DOM {city['dom']} days (moving fast)</div>
                            <div class="text-sm">• High absorption rate: {city['absorption_rate']}%</div>
                            <div class="text-sm text-red-400 mt-2">Strategy: List competitively, expect quick sale</div>
                        </div>
'''

    html += f'''                    </div>
                </div>
            </div>

            <!-- Market Prediction -->
            <div class="p-4 bg-blue-500/10 border-l-4 border-blue-500 rounded">
                <h3 class="text-lg font-bold text-blue-400 mb-2">Market Prediction & Strategy</h3>
                <div class="text-sm space-y-2">
                    <p><strong>Current State:</strong> {metro} is a {market_type_lower} with {months_supply} months of supply.
                    Inventory {inventory_yoy_str} YoY,
                    DOM {dom_yoy_str} YoY.</p>
                    <p><strong>Flipper Strategy:</strong></p>
                    <ul class="list-disc ml-5 space-y-1">
'''

    # Generate strategy based on market type
    if months_supply > 6:
        html += '''                        <li><strong>Acquisitions:</strong> NOW is the time to buy. Target cities with 5+ months supply. Negotiate aggressively - aim for 85-90% of list price.</li>
                        <li><strong>Active Flips:</strong> Accelerate renovations. Market favors buyers, so price competitively and consider incentives.</li>
                        <li><strong>Hold Strategy:</strong> Quick 60-90 day flips recommended. Don't hold inventory >4 months in buyer's market.</li>
                        <li><strong>Avoid:</strong> Major renovations with >90 day timelines. Market trending toward buyer's advantage.</li>
'''
    elif months_supply < 5:
        html += '''                        <li><strong>Acquisitions:</strong> Be selective. Seller's market means less negotiating power. Focus on distressed properties only.</li>
                        <li><strong>Active Flips:</strong> If you have inventory, LIST NOW. Strong seller's market with low supply.</li>
                        <li><strong>Hold Strategy:</strong> Can afford 90-120 day flips. Market will absorb inventory quickly.</li>
                        <li><strong>Opportunity:</strong> Consider wholesale assignments - demand outpaces supply.</li>
'''
    else:
        html += '''                        <li><strong>Acquisitions:</strong> Balanced market - fair negotiation possible. Target 5-10% below list for motivated sellers.</li>
                        <li><strong>Active Flips:</strong> Price at market value. Properties moving at steady pace.</li>
                        <li><strong>Hold Strategy:</strong> Standard 90 day flips are safe. Market is stable.</li>
                        <li><strong>Monitor:</strong> Watch for market shifts - could go either direction.</li>
'''

    html += f'''                    </ul>
                    <p class="mt-3 text-yellow-400"><strong>Risk Alert:</strong> {risk_alert}</p>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="card p-6 text-white text-center text-sm text-gray-400">
            <p>Dashboard generated from Redfin Market Tracker data</p>
        </div>

    </div>
'''

    # Build JavaScript section separately
    html += '''
    <script>
        // Chart defaults
        Chart.defaults.color = '#9ca3af';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

        const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
        const decimalFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        const percentFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#e5e7eb' } },
                tooltip: {
                    backgroundColor: 'rgba(15, 52, 96, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#e5e7eb',
                    callbacks: {
                        label: buildTooltipLabel
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af' }
                }
            }
        };

        const rangeButtonDefaultClass = 'px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium';
        const rangeButtonActiveClass = 'px-4 py-2 bg-blue-500/40 border-2 border-blue-500 rounded-lg text-sm font-bold';
        const cityRangeDefaultClass = 'city-range-button px-3 py-1 bg-white/10 border border-white/20 rounded';
        const cityRangeActiveClass = 'city-range-button px-3 py-1 bg-blue-500/40 border border-blue-500 text-white font-semibold rounded';

        // Data (12-month embedded for fast initial load)
        let defaultPeriods = ''' + periods_json + ''';
        let labels = ''' + labels_json + ''';
        const inventoryData = ''' + inventory_json + ''';
        const newListingsData = ''' + new_listings_json + ''';
        const pendingData = ''' + pending_json + ''';
        const priceDropsData = ''' + price_drops_json + ''';
        const domData = ''' + dom_json + ''';
        const pendingRatioData = ''' + pending_ratio_json + ''';
        const homesSoldData = ''' + homes_sold_json + ''';
        const medianPriceData = ''' + median_price_json + ''';
        const currentPeriod = ''' + period_json + ''';

        const periodIndexFull = ''' + period_index_full_json + ''';
        const periodIndex12 = ''' + period_index_12m_json + ''';
        const periodIndexByCity = ''' + period_index_by_city_json + ''';

        const inventoryMomData = ''' + inventory_mom_json + ''';
        const inventoryYoyData = ''' + inventory_yoy_json + ''';
        const newListingsMomData = ''' + new_listings_mom_json + ''';
        const newListingsYoyData = ''' + new_listings_yoy_json + ''';
        const pendingSalesMomData = ''' + pending_sales_mom_json + ''';
        const pendingSalesYoyData = ''' + pending_sales_yoy_json + ''';
        const homesSoldMomData = ''' + homes_sold_mom_json + ''';
        const homesSoldYoyData = ''' + homes_sold_yoy_json + ''';
        const priceDropsMomData = ''' + price_drops_mom_json + ''';
        const priceDropsYoyData = ''' + price_drops_yoy_json + ''';
        const domMomData = ''' + dom_mom_json + ''';
        const domYoyData = ''' + dom_yoy_json + ''';
        const priceMomData = ''' + price_mom_json + ''';
        const priceYoyData = ''' + price_yoy_json + ''';
        const pendingRatioMomData = ''' + pending_ratio_mom_json + ''';
        const pendingRatioYoyData = ''' + pending_ratio_yoy_json + ''';
        const monthsSupplySeries = ''' + months_supply_series_json + ''';
        const absorptionRateSeries = ''' + absorption_rate_json + ''';
        const supplyDemandSeries = ''' + supply_demand_series_json + ''';

        // City trends data (12-month default, top 5 cities)
        const cityTrends = ''' + city_trends_json + ''';
        const fullMetroTrends = ''' + full_metro_trends_json + ''';
        const fullCityTrends = ''' + full_city_trends_json + ''';
        const availableCities = ''' + available_cities_json + ''';
        const orderedCityNames = ''' + city_names_json + ''';

        const urlState = new URLSearchParams(window.location.hash ? window.location.hash.substring(1) : '');
        const getStoredValue = key => { try { return localStorage.getItem(key); } catch (e) { return null; } };
        const setStoredValue = (key, value) => { try { localStorage.setItem(key, value); } catch (e) {} };
        const removeStoredValue = key => { try { localStorage.removeItem(key); } catch (e) {} };
        const parseStoredArray = value => { try { return JSON.parse(value || '[]'); } catch (e) { return []; } };

        const initialRangeFromUrl = urlState.get('range');
        const initialCityFromUrl = urlState.get('city');
        const initialMetricFromUrl = urlState.get('metric');
        const initialMultiMetricFromUrl = urlState.get('multiMetric');
        const initialMultiCitiesFromUrl = (urlState.get('multiCities') || '').split(',').filter(Boolean);
        const initialMetroOverlayFromUrl = urlState.get('metroOverlay') === '1';
        const hasMetroOverlayParam = urlState.has('metroOverlay');

        let initialRange = initialRangeFromUrl || getStoredValue('date_range') || '12m';

        // Current date range state
        let currentRange = initialRange;
        let filteredMetroData = null;

        // Format period labels helper
        function formatLabels(periods) {
            return periods.map(period => {
                const [year, month] = period.split('-');
                const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                return monthNames[parseInt(month)] + " '" + year.slice(2);
            });
        }

        if (Array.isArray(periodIndex12) && periodIndex12.length) {
            defaultPeriods = periodIndex12.slice();
            labels = formatLabels(defaultPeriods);
        } else if (!Array.isArray(labels) || labels.length === 0) {
            labels = formatLabels(defaultPeriods);
        }

        function getEmbeddedMetroData() {
            return {
                data: null,
                label: 'Last 12 Months (Default)',
                periods: defaultPeriods.slice(),
                labels: labels.slice(),
                inventory: inventoryData.slice(),
                new_listings: newListingsData.slice(),
                pending_sales: pendingData.slice(),
                homes_sold: homesSoldData.slice(),
                price_drops: priceDropsData.slice(),
                median_dom: domData.slice(),
                median_sale_price: medianPriceData.slice(),
                pending_ratio: pendingRatioData.slice(),
                inventory_mom: inventoryMomData.slice(),
                inventory_yoy: inventoryYoyData.slice(),
                new_listings_mom: newListingsMomData.slice(),
                new_listings_yoy: newListingsYoyData.slice(),
                pending_sales_mom: pendingSalesMomData.slice(),
                pending_sales_yoy: pendingSalesYoyData.slice(),
                homes_sold_mom: homesSoldMomData.slice(),
                homes_sold_yoy: homesSoldYoyData.slice(),
                price_drops_mom: priceDropsMomData.slice(),
                price_drops_yoy: priceDropsYoyData.slice(),
                median_dom_mom: domMomData.slice(),
                median_dom_yoy: domYoyData.slice(),
                median_sale_price_mom: priceMomData.slice(),
                median_sale_price_yoy: priceYoyData.slice(),
                pending_ratio_mom: pendingRatioMomData.slice(),
                pending_ratio_yoy: pendingRatioYoyData.slice(),
                months_of_supply: monthsSupplySeries.slice(),
                absorption_rate: absorptionRateSeries.slice(),
                supply_demand_ratio: supplyDemandSeries.slice()
            };
        }

        // Filter metro data by date range
        function filterDataByRange(range) {
            if (!Array.isArray(fullMetroTrends) || fullMetroTrends.length === 0) {
                return getEmbeddedMetroData();
            }

            const now = new Date(currentPeriod + '-01');
            let cutoffDate;
            let rangeLabel = '';

            if (range === '6m') {
                cutoffDate = new Date(now.getFullYear(), now.getMonth() - 5, 1);
                rangeLabel = 'Last 6 Months';
            } else if (range === '12m') {
                cutoffDate = new Date(now.getFullYear(), now.getMonth() - 11, 1);
                rangeLabel = 'Last 12 Months (Default)';
            } else if (range === 'ytd') {
                cutoffDate = new Date(now.getFullYear(), 0, 1);
                rangeLabel = 'YTD ' + now.getFullYear();
            } else if (range === '2y') {
                cutoffDate = new Date(now.getFullYear() - 2, now.getMonth(), 1);
                rangeLabel = 'Last 2 Years';
            } else if (range === '5y') {
                cutoffDate = new Date(now.getFullYear() - 5, now.getMonth(), 1);
                rangeLabel = 'Last 5 Years';
            } else if (range === 'all') {
                cutoffDate = new Date('2000-01-01');
                rangeLabel = 'All Time (' + fullMetroTrends.length + ' months)';
            } else {
                cutoffDate = new Date(now.getFullYear(), now.getMonth() - 11, 1);
                rangeLabel = 'Last 12 Months (Default)';
            }

            const cutoffStr = cutoffDate.toISOString().slice(0, 7);
            const filtered = fullMetroTrends.filter(t => t.period >= cutoffStr);
            const effective = filtered.length > 0 ? filtered : fullMetroTrends.slice(-12);
            const labelText = filtered.length > 0 ? rangeLabel : 'Last 12 Months (Default)';

            return {
                data: effective,
                label: labelText,
                periods: effective.map(t => t.period),
                labels: formatLabels(effective.map(t => t.period)),
                inventory: effective.map(t => t.inventory),
                new_listings: effective.map(t => t.new_listings),
                pending_sales: effective.map(t => t.pending_sales),
                homes_sold: effective.map(t => t.homes_sold),
                price_drops: effective.map(t => t.price_drops),
                median_dom: effective.map(t => t.median_dom),
                median_sale_price: effective.map(t => t.median_sale_price),
                pending_ratio: effective.map(t => (t.pending_ratio ?? null)),
                inventory_mom: effective.map(t => t.inventory_mom ?? null),
                inventory_yoy: effective.map(t => t.inventory_yoy ?? null),
                new_listings_mom: effective.map(t => t.new_listings_mom ?? null),
                new_listings_yoy: effective.map(t => t.new_listings_yoy ?? null),
                pending_sales_mom: effective.map(t => t.pending_sales_mom ?? null),
                pending_sales_yoy: effective.map(t => t.pending_sales_yoy ?? null),
                homes_sold_mom: effective.map(t => t.homes_sold_mom ?? null),
                homes_sold_yoy: effective.map(t => t.homes_sold_yoy ?? null),
                price_drops_mom: effective.map(t => t.price_drops_mom ?? null),
                price_drops_yoy: effective.map(t => t.price_drops_yoy ?? null),
                median_dom_mom: effective.map(t => t.median_dom_mom ?? null),
                median_dom_yoy: effective.map(t => t.median_dom_yoy ?? null),
                median_sale_price_mom: effective.map(t => t.median_sale_price_mom ?? null),
                median_sale_price_yoy: effective.map(t => t.median_sale_price_yoy ?? null),
                pending_ratio_mom: effective.map(t => t.pending_ratio_mom ?? null),
                pending_ratio_yoy: effective.map(t => t.pending_ratio_yoy ?? null),
                months_of_supply: effective.map(t => t.months_of_supply ?? null),
                absorption_rate: effective.map(t => t.absorption_rate ?? null),
                supply_demand_ratio: effective.map(t => t.supply_demand_ratio ?? null)
            };
        }

        function syncUrlState() {
            try {
                const params = new URLSearchParams();
                if (currentRange) params.set('range', currentRange);
                if (currentCity) params.set('city', currentCity);
                if (currentCityMetricMode && currentCityMetricMode !== 'all') params.set('metric', currentCityMetricMode);
                if (currentCityRange && currentCityRange !== '24m') params.set('cityRange', currentCityRange);
                if (selectedCities.length) params.set('multiCities', selectedCities.join(','));
                if (multiCityMetric && multiCityMetric !== 'inventory') params.set('multiMetric', multiCityMetric);
                const metroOverlayChecked = document.getElementById('multiCityMetro')?.checked;
                if (metroOverlayChecked) params.set('metroOverlay', '1');
                const hash = params.toString();
                const base = window.location.pathname + window.location.search;
                const newUrl = hash ? base + '#' + hash : base;
                if (window.location.href !== newUrl) {
                    window.history.replaceState(null, '', newUrl);
                }
            } catch (e) {
                console.warn('Unable to sync URL state', e);
            }
        }

        // Initialize with saved or default range
        try {
            filteredMetroData = filterDataByRange(initialRange);
            console.log('Filtered data initialized:', filteredMetroData ? 'SUCCESS' : 'FAILED');
        } catch (e) {
            console.error('Error initializing filtered data:', e);
            alert('Error loading chart data: ' + e.message);
            initialRange = '12m';
            currentRange = '12m';
            filteredMetroData = filterDataByRange('12m');
        }
        currentRange = initialRange;

        // ============= MOVING AVERAGES & TREND LINES =============

        // Calculate Simple Moving Average
        function calculateSMA(data, period) {
            const result = [];
            for (let i = 0; i < data.length; i++) {
                if (i < period - 1) {
                    result.push(null);  // Not enough data points yet
                } else {
                    let sum = 0;
                    for (let j = 0; j < period; j++) {
                        sum += data[i - j] || 0;
                    }
                    result.push(sum / period);
                }
            }
            return result;
        }

        // Calculate linear regression trend line
        function calculateTrendLine(data) {
            const n = data.length;
            let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;

            for (let i = 0; i < n; i++) {
                const x = i;
                const y = data[i] || 0;
                sumX += x;
                sumY += y;
                sumXY += x * y;
                sumXX += x * x;
            }

            const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
            const intercept = (sumY - slope * sumX) / n;

            return data.map((_, i) => slope * i + intercept);
        }

        function formatMetricValue(metricKey, value) {
            if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
            const numericValue = Number(value);
            if (Number.isNaN(numericValue)) return 'N/A';
            if (!metricKey) {
                return Number.isFinite(numericValue) ? decimalFormatter.format(numericValue) : String(value);
            }

            switch (metricKey) {
                case 'inventory':
                case 'new_listings':
                case 'pending_sales':
                case 'homes_sold':
                case 'price_drops':
                    return numberFormatter.format(numericValue);
                case 'median_dom':
                    return `${Math.round(numericValue)} days`;
                case 'median_sale_price':
                    return currencyFormatter.format(numericValue);
                case 'pending_ratio':
                case 'absorption_rate':
                    return `${(numericValue * 100).toFixed(1)}%`;
                case 'months_of_supply':
                    return `${numericValue.toFixed(1)} mo`;
                case 'supply_demand_ratio':
                    return numericValue.toFixed(2);
                default:
                    return Number.isFinite(numericValue) ? decimalFormatter.format(numericValue) : String(value);
            }
        }

        function formatDelta(delta, label) {
            if (delta === null || delta === undefined || Number.isNaN(delta)) return null;
            const numericDelta = Number(delta);
            if (!Number.isFinite(numericDelta)) return null;
            const pct = Math.abs(numericDelta) * 100;
            const decimals = pct >= 10 ? 1 : 2;
            const arrow = numericDelta > 0 ? '▲' : numericDelta < 0 ? '▼' : '●';
            return `${arrow} ${pct.toFixed(decimals)}% ${label}`;
        }

        function buildTooltipLabel(context) {
            const dataset = context.dataset || {};
            const value = context.parsed?.y;
            const metricKey = dataset.metaKey;
            const labelValue = formatMetricValue(metricKey, value);
            let output = `${dataset.label}: ${labelValue}`;

            const source = typeof dataset.tooltipSource === 'function' ? dataset.tooltipSource() : filteredMetroData;
            if (source && metricKey) {
                const derived = derivedKeysForMetricKey(metricKey);
                const momSeries = source[derived.mom];
                const yoySeries = source[derived.yoy];
                if (momSeries && momSeries.length > context.dataIndex) {
                    const formatted = formatDelta(momSeries[context.dataIndex], 'MoM');
                    if (formatted) output += '\\n  ' + formatted;
                }
                if (yoySeries && yoySeries.length > context.dataIndex) {
                    const formatted = formatDelta(yoySeries[context.dataIndex], 'YoY');
                    if (formatted) output += '\\n  ' + formatted;
                }
            }

            return output;
        }

        // Set date range and update all charts
        function setDateRange(range, clickedButton) {
            currentRange = range;
            filteredMetroData = filterDataByRange(range);

            // Update date range display
            document.getElementById('dateRangeDisplay').textContent = filteredMetroData.label;

            // Update chart titles
            const suffix = ' (' + filteredMetroData.label + ')';
            document.getElementById('inventoryChartTitle').textContent = 'Metro Inventory Dynamics' + suffix;
            document.getElementById('priceDropsChartTitle').textContent = 'Price Reductions' + suffix;
            document.getElementById('supplyDemandChartTitle').textContent = 'Supply vs Demand Balance' + suffix;
            document.getElementById('domPendingChartTitle').textContent = 'Days on Market & Pending Ratio' + suffix;

            // Update all charts
            updateInventoryChart();
            updatePriceDropsChart();
            updateSupplyDemandChart();
            updateDomPendingChart();

            // Update active button styling
            document.querySelectorAll('[data-range]').forEach(btn => {
                btn.className = rangeButtonDefaultClass;
            });
            const buttonToActivate = clickedButton || document.querySelector(`[data-range="${range}"]`);
            if (buttonToActivate) {
                buttonToActivate.className = rangeButtonActiveClass;
            }
            setStoredValue('date_range', range);
            syncUrlState();
        }

        // Inventory Chart (Dynamic)
        let inventoryChart;
        try {
            if (!filteredMetroData) {
                throw new Error('filteredMetroData is not initialized');
            }
            inventoryChart = new Chart(document.getElementById('inventoryChart'), {
                type: 'line',
                data: {
                    labels: filteredMetroData.labels,
                    datasets: [
                        {
                            label: 'Active Listings',
                            data: filteredMetroData.inventory,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.4,
                            metaKey: 'inventory',
                            tooltipSource: () => filteredMetroData
                        },
                        {
                            label: 'New Listings',
                            data: filteredMetroData.new_listings,
                            borderColor: '#10b981',
                            tension: 0.4,
                            metaKey: 'new_listings',
                            tooltipSource: () => filteredMetroData
                        },
                        {
                            label: 'Pending Sales',
                            data: filteredMetroData.pending_sales,
                            borderColor: '#f59e0b',
                            tension: 0.4,
                            metaKey: 'pending_sales',
                            tooltipSource: () => filteredMetroData
                        }
                    ]
                },
                options: chartOptions
            });
            console.log('Inventory chart created successfully');
        } catch (e) {
            console.error('Error creating inventory chart:', e);
        }

        // Update inventory chart function
        function updateInventoryChart() {
            const value = document.getElementById('inventoryMetric').value;
            inventoryChart.data.labels = filteredMetroData.labels;

            // Base datasets
            let datasets = [];
            if (value === 'all') {
                datasets = [
                    { label: 'Active Listings', data: filteredMetroData.inventory, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.4, borderWidth: 2,
                        metaKey: 'inventory', tooltipSource: () => filteredMetroData },
                    { label: 'New Listings', data: filteredMetroData.new_listings, borderColor: '#10b981', tension: 0.4, borderWidth: 2,
                        metaKey: 'new_listings', tooltipSource: () => filteredMetroData },
                    { label: 'Pending Sales', data: filteredMetroData.pending_sales, borderColor: '#f59e0b', tension: 0.4, borderWidth: 2,
                        metaKey: 'pending_sales', tooltipSource: () => filteredMetroData }
                ];
            } else if (value === 'inventory') {
                datasets = [
                    { label: 'Active Listings', data: filteredMetroData.inventory, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.4, borderWidth: 2,
                        metaKey: 'inventory', tooltipSource: () => filteredMetroData }
                ];
            } else if (value === 'new_listings') {
                datasets = [
                    { label: 'New Listings', data: filteredMetroData.new_listings, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.4, borderWidth: 2,
                        metaKey: 'new_listings', tooltipSource: () => filteredMetroData }
                ];
            } else if (value === 'pending') {
                datasets = [
                    { label: 'Pending Sales', data: filteredMetroData.pending_sales, borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', fill: true, tension: 0.4, borderWidth: 2,
                        metaKey: 'pending_sales', tooltipSource: () => filteredMetroData }
                ];
            }

            if (!datasets.length) {
                inventoryChart.data.datasets = [];
                inventoryChart.update();
                return;
            }

            // Add moving averages if enabled
            const primaryData = datasets[0].data;
            if (document.getElementById('showMA3').checked) {
                datasets.push({
                    label: '3-Month MA',
                    data: calculateSMA(primaryData, 3),
                    borderColor: '#ec4899',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0
                });
            }
            if (document.getElementById('showMA6').checked) {
                datasets.push({
                    label: '6-Month MA',
                    data: calculateSMA(primaryData, 6),
                    borderColor: '#a855f7',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0
                });
            }
            if (document.getElementById('showMA12').checked) {
                datasets.push({
                    label: '12-Month MA',
                    data: calculateSMA(primaryData, 12),
                    borderColor: '#14b8a6',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0
                });
            }
            if (document.getElementById('showTrendLine').checked) {
                datasets.push({
                    label: 'Trend Line',
                    data: calculateTrendLine(primaryData),
                    borderColor: '#fbbf24',
                    borderDash: [2, 2],
                    borderWidth: 2,
                    tension: 0,
                    pointRadius: 0
                });
            }

            inventoryChart.data.datasets = datasets;
            inventoryChart.update();
        }

        // Toggle moving averages
        function toggleMovingAverages() {
            updateInventoryChart();
        }

        // Update inventory chart based on dropdown
        document.getElementById('inventoryMetric').addEventListener('change', updateInventoryChart);

        // Price Drops Chart
        let priceDropsChart = new Chart(document.getElementById('priceDropsChart'), {
            type: 'bar',
            data: {
                labels: filteredMetroData.labels,
                datasets: [{
                    label: 'Price Reductions',
                    data: filteredMetroData.price_drops,
                    backgroundColor: '#ef4444',
                    metaKey: 'price_drops',
                    tooltipSource: () => filteredMetroData
                }]
            },
            options: chartOptions
        });

        // Update price drops chart function
        function updatePriceDropsChart() {
            priceDropsChart.data.labels = filteredMetroData.labels;
            priceDropsChart.data.datasets[0].data = filteredMetroData.price_drops;
            priceDropsChart.update();
        }

        // Supply vs Demand Chart
        let supplyDemandChart = new Chart(document.getElementById('supplyDemandChart'), {
            type: 'line',
            data: {
                labels: filteredMetroData.labels,
                datasets: [
                    {
                        label: 'New Listings (Supply)',
                        data: filteredMetroData.new_listings,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.4,
                        metaKey: 'new_listings',
                        tooltipSource: () => filteredMetroData
                    },
                    {
                        label: 'Homes Sold (Demand)',
                        data: filteredMetroData.homes_sold,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        metaKey: 'homes_sold',
                        tooltipSource: () => filteredMetroData
                    }
                ]
            },
            options: chartOptions
        });

        // Update supply demand chart function
        function updateSupplyDemandChart() {
            supplyDemandChart.data.labels = filteredMetroData.labels;
            supplyDemandChart.data.datasets[0].data = filteredMetroData.new_listings;
            supplyDemandChart.data.datasets[1].data = filteredMetroData.homes_sold;
            supplyDemandChart.update();
        }

        // Combined DOM + Pending Ratio Chart
        let domPendingChart = new Chart(document.getElementById('domPendingChart'), {
            type: 'line',
            data: {
                labels: filteredMetroData.labels,
                datasets: [
                    {
                        label: 'Days on Market',
                        data: filteredMetroData.median_dom,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y',
                        metaKey: 'median_dom',
                        tooltipSource: () => filteredMetroData
                    },
                    {
                        label: 'Pending Ratio',
                        data: filteredMetroData.pending_ratio,
                        borderColor: '#f59e0b',
                        tension: 0.4,
                        yAxisID: 'y1',
                        metaKey: 'pending_ratio',
                        tooltipSource: () => filteredMetroData
                    }
                ]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af' },
                        title: { display: true, text: 'Days on Market', color: '#8b5cf6' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        grid: { display: false },
                        ticks: { color: '#9ca3af' },
                        title: { display: true, text: 'Pending Ratio', color: '#f59e0b' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af' }
                    }
                }
            }
        });

        // Update DOM + Pending chart function
        function updateDomPendingChart() {
            domPendingChart.data.labels = filteredMetroData.labels;
            domPendingChart.data.datasets[0].data = filteredMetroData.median_dom;
            domPendingChart.data.datasets[1].data = filteredMetroData.pending_ratio;
            domPendingChart.update();
        }

        // City Chart (Dynamic)
        const cityNames = orderedCityNames.slice();
        const legacyMetricMap = { sales: 'homes_sold', dom: 'median_dom', price: 'median_sale_price' };

        const storedCity = getStoredValue('cityChartCity');
        let currentCity = cityNames.includes(initialCityFromUrl) ? initialCityFromUrl : (storedCity && cityNames.includes(storedCity) ? storedCity : cityNames[0]);

        let storedCityMetric = getStoredValue('cityChartMetric');
        if (storedCityMetric && legacyMetricMap[storedCityMetric]) storedCityMetric = legacyMetricMap[storedCityMetric];
        const mappedMetricFromUrl = initialMetricFromUrl && legacyMetricMap[initialMetricFromUrl] ? legacyMetricMap[initialMetricFromUrl] : initialMetricFromUrl;

        const cityMetricModes = ['all','inventory','new_listings','pending_sales','homes_sold','median_sale_price','median_dom'];
        const storedCityRange = getStoredValue('city_range');
        const cityRangeOptions = ['12m','24m','60m','all'];
        const initialCityRangeFromUrl = urlState.get('cityRange');

        let currentCityMetricMode = cityMetricModes.includes(mappedMetricFromUrl) ? mappedMetricFromUrl : (cityMetricModes.includes(storedCityMetric) ? storedCityMetric : 'all');
        let currentCityRange = cityRangeOptions.includes(initialCityRangeFromUrl) ? initialCityRangeFromUrl : (cityRangeOptions.includes(storedCityRange) ? storedCityRange : '24m');

        function getCitySeries(city) {
            return fullCityTrends[city] || cityTrends[city] || [];
        }

        function getCityPeriods(city, range = currentCityRange) {
            const series = getCitySeries(city);
            const base = periodIndexByCity[city] || series.map(t => t.period);
            if (!base.length || !series.length) return series.map(t => t.period);
            const total = Math.min(base.length, series.length);
            let take = total;
            if (range === '12m') take = Math.min(12, total);
            else if (range === '24m') take = Math.min(24, total);
            else if (range === '60m') take = Math.min(60, total);
            // 'all' retains full length
            const startIndex = total - take;
            return base.slice(startIndex, startIndex + take);
        }

        let cityPeriods = getCityPeriods(currentCity, currentCityRange);
        let cityLabels = formatLabels(cityPeriods);

        function resolveMetricKey(metric) {
            if (metric === 'inventory') return 'inventory';
            if (metric === 'new_listings') return 'new_listings';
            if (metric === 'pending_sales' || metric === 'pending') return 'pending_sales';
            if (metric === 'homes_sold' || metric === 'sales') return 'homes_sold';
            if (metric === 'median_dom' || metric === 'dom') return 'median_dom';
            if (metric === 'median_sale_price' || metric === 'price') return 'median_sale_price';
            return metric;
        }

        function derivedKeysForMetricKey(metricKey) {
            return {
                mom: metricKey + '_mom',
                yoy: metricKey + '_yoy'
            };
        }

        function getCityData(city, metric) {
            const key = resolveMetricKey(metric);
            const series = getCitySeries(city);
            return series.map(t => t[key] ?? null);
        }

        function getMetricLabel(metric) {
            switch (metric) {
                case 'inventory':
                    return 'Inventory';
                case 'new_listings':
                    return 'New Listings';
                case 'pending_sales':
                case 'pending':
                    return 'Pending Sales';
                case 'homes_sold':
                case 'sales':
                    return 'Homes Sold';
                case 'median_dom':
                case 'dom':
                    return 'Days on Market';
                case 'median_sale_price':
                case 'price':
                    return 'Median Sale Price';
                default:
                    return metric;
            }
        }

        function getMetricColor(metric) {
            switch (metric) {
                case 'inventory':
                    return '#3b82f6';
                case 'new_listings':
                    return '#10b981';
                case 'pending_sales':
                case 'pending':
                    return '#f59e0b';
                case 'homes_sold':
                case 'sales':
                    return '#ef4444';
                case 'median_dom':
                case 'dom':
                    return '#8b5cf6';
                case 'median_sale_price':
                case 'price':
                    return '#f97316';
                default:
                    return '#3b82f6';
            }
        }

        function getCityTooltipSource(city) {
            const series = getCitySeries(city);
            const base = ['inventory', 'new_listings', 'pending_sales', 'homes_sold', 'median_dom', 'median_sale_price'];
            const result = {};
            base.forEach(key => {
                result[key] = series.map(t => t[key] ?? null);
                const derived = derivedKeysForMetricKey(key);
                result[derived.mom] = series.map(t => t[derived.mom] ?? null);
                result[derived.yoy] = series.map(t => t[derived.yoy] ?? null);
            });
            return result;
        }

        function buildCityDatasets() {
            const series = getCitySeries(currentCity);
            const periods = getCityPeriods(currentCity, currentCityRange);
            const take = Math.min(periods.length, series.length);
            const startIndex = Math.max(0, series.length - take);
            const tooltipSource = getCityTooltipSource(currentCity);
            const metricKey = resolveMetricKey(currentCityMetricMode);

            if (currentCityMetricMode === 'all') {
                const configs = [
                    { key: 'inventory' },
                    { key: 'new_listings' },
                    { key: 'pending_sales' },
                    { key: 'homes_sold' }
                ];
                return configs.map(cfg => ({
                    label: getMetricLabel(cfg.key),
                    data: series.slice(startIndex).map(t => t[cfg.key] ?? null),
                    borderColor: getMetricColor(cfg.key),
                    backgroundColor: getMetricColor(cfg.key) + '20',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    metaKey: cfg.key,
                    tooltipSource: () => tooltipSource
                }));
            }

            const baseData = series.slice(startIndex).map(t => t[metricKey] ?? null);
            const datasets = [{
                label: getMetricLabel(metricKey),
                data: baseData,
                borderColor: getMetricColor(metricKey),
                backgroundColor: getMetricColor(metricKey) + '20',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                metaKey: metricKey,
                tooltipSource: () => tooltipSource
            }];

            const ma3 = document.getElementById('cityShowMA3');
            const ma6 = document.getElementById('cityShowMA6');
            const ma12 = document.getElementById('cityShowMA12');
            const showTrend = document.getElementById('cityShowTrend');

            if (ma3?.checked) {
                datasets.push({
                    label: getMetricLabel(metricKey) + ' (3-Mo MA)',
                    data: calculateSMA(baseData, 3),
                    borderColor: '#ec4899',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    metaKey: null
                });
            }
            if (ma6?.checked) {
                datasets.push({
                    label: getMetricLabel(metricKey) + ' (6-Mo MA)',
                    data: calculateSMA(baseData, 6),
                    borderColor: '#a855f7',
                    borderDash: [6, 4],
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    metaKey: null
                });
            }
            if (ma12?.checked) {
                datasets.push({
                    label: getMetricLabel(metricKey) + ' (12-Mo MA)',
                    data: calculateSMA(baseData, 12),
                    borderColor: '#14b8a6',
                    borderDash: [8, 4],
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    metaKey: null
                });
            }
            if (showTrend?.checked) {
                datasets.push({
                    label: getMetricLabel(metricKey) + ' (Trend)',
                    data: calculateTrendLine(baseData),
                    borderColor: '#fbbf24',
                    borderDash: [2, 2],
                    borderWidth: 2,
                    tension: 0,
                    pointRadius: 0,
                    metaKey: null
                });
            }

            return datasets;
        }

        function getMultiCityTooltipSource(city) {
            const series = (fullCityTrends[city] || cityTrends[city] || []);
            const base = ['inventory', 'homes_sold', 'median_dom', 'median_sale_price'];
            const result = {};
            base.forEach(key => {
                result[key] = series.map(t => t[key] ?? null);
                const derived = derivedKeysForMetricKey(key);
                result[derived.mom] = series.map(t => t[derived.mom] ?? null);
                result[derived.yoy] = series.map(t => t[derived.yoy] ?? null);
            });
            return result;
        }

        function updateCityToggleState() {
            const disable = currentCityMetricMode === 'all';
            ['cityShowMA3','cityShowMA6','cityShowMA12','cityShowTrend'].forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.disabled = disable;
                    if (disable) el.checked = false;
                }
            });
        }

        function updateCityChart() {
            cityPeriods = getCityPeriods(currentCity, currentCityRange);
            cityLabels = formatLabels(cityPeriods);
            cityChart.data.labels = cityLabels;
            cityChart.data.datasets = buildCityDatasets();
            cityChart.update();
        }

        let cityChart = new Chart(document.getElementById('cityChart'), {
            type: 'line',
            data: {
                labels: cityLabels,
                datasets: buildCityDatasets()
            },
            options: chartOptions
        });

        const citySelectEl = document.getElementById('citySelector');
        const metricSelectEl = document.getElementById('cityMetricMode');
        if (citySelectEl && cityNames.includes(currentCity)) citySelectEl.value = currentCity;
        if (metricSelectEl) metricSelectEl.value = currentCityMetricMode;
        updateCityToggleState();

        function setCityRange(range, clickedButton) {
            if (!cityRangeOptions.includes(range)) range = '24m';
            currentCityRange = range;
            setStoredValue('city_range', currentCityRange);

            document.querySelectorAll('.city-range-button').forEach(btn => btn.className = cityRangeDefaultClass);
            const buttonToActivate = clickedButton || document.querySelector(`[data-city-range="${currentCityRange}"]`);
            if (buttonToActivate) buttonToActivate.className = cityRangeActiveClass;

            updateCityChart();
            syncUrlState();
        }

        document.getElementById('citySelector').addEventListener('change', function(e) {
            currentCity = e.target.value;
            setStoredValue('cityChartCity', currentCity);
            updateCityChart();
            syncUrlState();
        });

        document.getElementById('cityMetricMode').addEventListener('change', function(e) {
            currentCityMetricMode = e.target.value;
            if (!cityMetricModes.includes(currentCityMetricMode)) currentCityMetricMode = 'all';
            setStoredValue('cityChartMetric', currentCityMetricMode);
            updateCityToggleState();
            updateCityChart();
            syncUrlState();
        });

        ['cityShowMA3','cityShowMA6','cityShowMA12','cityShowTrend'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => {
                if (currentCityMetricMode !== 'all') {
                    updateCityChart();
                }
            });
        });

        document.querySelectorAll('.city-range-button').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                setCityRange(btn.getAttribute('data-city-range'), btn);
            });
        });

        // Initial state for city range buttons
        setCityRange(currentCityRange, document.querySelector(`[data-city-range="${currentCityRange}"]`));

        // Apply initial range selection to update titles and button state
        setTimeout(() => {
            const btn = document.querySelector(`[data-range="${initialRange}"]`);
            setDateRange(initialRange, btn);
        }, 0);

        // ============= MULTI-CITY COMPARISON TOOL =============

        // Generate distinct colors for cities
        const cityColors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
            '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16',
            '#a855f7', '#22c55e', '#eab308', '#6366f1', '#f43f5e',
            '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
        ];

        const storedMultiCities = parseStoredArray(getStoredValue('mc_selected_cities'));
        let selectedCities = Array.from(new Set((initialMultiCitiesFromUrl.length ? initialMultiCitiesFromUrl : storedMultiCities))).filter(city => availableCities.includes(city)).slice(0, 10);

        const multiMetricOptions = ['inventory','sales','dom','price'];
        const storedMultiMetric = getStoredValue('mc_metric');
        let multiCityMetric = initialMultiMetricFromUrl || storedMultiMetric || 'inventory';
        if (!multiMetricOptions.includes(multiCityMetric)) multiCityMetric = 'inventory';

        // Generate checkbox list
        function generateCityCheckboxes() {
            const container = document.getElementById('cityCheckboxList');
            container.innerHTML = '';

            availableCities.forEach((city, index) => {
                const div = document.createElement('div');
                div.className = 'flex items-center gap-2 p-2 hover:bg-white/5 rounded cursor-pointer';
                div.innerHTML = `
                    <input type="checkbox" id="city_${index}" value="${city}"
                           class="city-checkbox w-4 h-4 cursor-pointer"
                           aria-label="Select ${city}"
                           onchange="toggleCity(this)">
                    <label for="city_${index}" class="cursor-pointer flex-1 text-sm">${city}</label>
                `;
                container.appendChild(div);
            });
        }

        // Toggle city selection
        function toggleCity(checkbox) {
            const city = checkbox.value;
            if (checkbox.checked) {
                if (selectedCities.includes(city)) {
                    return;
                }
                if (selectedCities.length < 10) {
                    selectedCities.push(city);
                } else {
                    checkbox.checked = false;
                    alert('Maximum 10 cities can be selected for comparison');
                    return;
                }
            } else {
                selectedCities = selectedCities.filter(c => c !== city);
            }
            updateSelectedCitiesList();
            updateMultiCityChart();
            setStoredValue('mc_selected_cities', JSON.stringify(selectedCities));
            syncUrlState();
        }

        // Update selected cities display
        function updateSelectedCitiesList() {
            const container = document.getElementById('selectedCitiesList');
            const count = document.getElementById('selectedCount');
            count.textContent = selectedCities.length;

            if (selectedCities.length === 0) {
                container.innerHTML = '<p class="text-gray-500">No cities selected. Use checkboxes to select cities.</p>';
            } else {
                container.innerHTML = selectedCities.map((city, i) => {
                    const color = cityColors[i % cityColors.length];
                    return `<div class="flex items-center gap-2 mb-1">
                        <div style="width:12px;height:12px;background:${color};border-radius:2px;"></div>
                        <span>${city}</span>
                    </div>`;
                }).join('');
            }
        }

        // Search cities
        document.getElementById('citySearch').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            document.querySelectorAll('#cityCheckboxList > div').forEach(div => {
                const label = div.querySelector('label').textContent.toLowerCase();
                div.style.display = label.includes(searchTerm) ? 'flex' : 'none';
            });
        });

        // Get city data for multi-city chart
        function getMultiCityData(city, metric) {
            const series = (fullCityTrends[city] || cityTrends[city]);
            if (!series) return [];
            const key = resolveMetricKey(metric);
            return series.map(t => t[key] ?? null);
        }

        // Build union of periods across selected cities (sorted)
        function getMultiCityPeriods() {
            if (selectedCities.length === 0) return [];
            const set = new Set();
            selectedCities.forEach(city => {
                const series = (fullCityTrends[city] || cityTrends[city] || []);
                series.forEach(t => set.add(t.period));
            });
            return Array.from(set).sort();
        }

        // Multi-city chart
        let multiCityChart = new Chart(document.getElementById('multiCityChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { color: '#e5e7eb', boxWidth: 12 }
                    }
                }
            }
        });

        // Update multi-city chart
        function updateMultiCityChart() {
            if (selectedCities.length === 0) {
                multiCityChart.data.labels = [];
                multiCityChart.data.datasets = [];
                multiCityChart.update();
                syncUrlState();
                return;
            }

            const periods = getMultiCityPeriods();
            const labels = formatLabels(periods);
            const datasets = [];
            const metricKey = resolveMetricKey(multiCityMetric);
            const metroMap = Object.fromEntries((fullMetroTrends || []).map(t => [t.period, t]));

            // Add main city data
            selectedCities.forEach((city, i) => {
                const color = cityColors[i % cityColors.length];
                const series = (fullCityTrends[city] || cityTrends[city] || []);
                const map = Object.fromEntries(series.map(t => [t.period, t]));
                const tooltipSource = getMultiCityTooltipSource(city);
                const base = periods.map(p => {
                    const t = map[p];
                    if (!t) return null;
                    return t[metricKey] ?? null;
                });

                datasets.push({
                    label: city,
                    data: base,
                    borderColor: color,
                    backgroundColor: color + '20',
                    tension: 0.4,
                    borderWidth: 2,
                    metaKey: metricKey,
                    tooltipSource: () => tooltipSource
                });

                // Add moving averages for each city if enabled
                if (document.getElementById('multiCityMA3').checked) {
                    datasets.push({
                        label: city + ' (3-Mo MA)',
                        data: calculateSMA(base, 3),
                        borderColor: color,
                        borderDash: [5, 5],
                        borderWidth: 1,
                        tension: 0.4,
                        pointRadius: 0,
                        metaKey: null
                    });
                }
                if (document.getElementById('multiCityMA6').checked) {
                    datasets.push({
                        label: city + ' (6-Mo MA)',
                        data: calculateSMA(base, 6),
                        borderColor: color,
                        borderDash: [8, 4],
                        borderWidth: 1,
                        tension: 0.4,
                        pointRadius: 0,
                        metaKey: null
                    });
                }
                if (document.getElementById('multiCityMA12').checked) {
                    datasets.push({
                        label: city + ' (12-Mo MA)',
                        data: calculateSMA(base, 12),
                        borderColor: color,
                        borderDash: [10, 3],
                        borderWidth: 1,
                        tension: 0.4,
                        pointRadius: 0,
                        metaKey: null
                    });
                }
                if (document.getElementById('multiCityTrend').checked) {
                    datasets.push({
                        label: city + ' (Trend)',
                        data: calculateTrendLine(base),
                        borderColor: color,
                        borderDash: [2, 2],
                        borderWidth: 1,
                        tension: 0,
                        pointRadius: 0,
                        metaKey: null
                    });
                }
            });

            const overlayEnabled = metroOverlayEl ? metroOverlayEl.checked : false;
            if (overlayEnabled && periods.length) {
                const derived = derivedKeysForMetricKey(metricKey);
                const metroTooltip = {};
                metroTooltip[metricKey] = periods.map(p => (metroMap[p] ? metroMap[p][metricKey] ?? null : null));
                metroTooltip[derived.mom] = periods.map(p => (metroMap[p] ? metroMap[p][derived.mom] ?? null : null));
                metroTooltip[derived.yoy] = periods.map(p => (metroMap[p] ? metroMap[p][derived.yoy] ?? null : null));

                datasets.push({
                    label: 'Metro Benchmark',
                    data: metroTooltip[metricKey],
                    borderColor: '#e5e7eb',
                    borderDash: [6, 4],
                    borderWidth: 2,
                    pointRadius: 0,
                    metaKey: metricKey,
                    tooltipSource: () => metroTooltip
                });
            }

            multiCityChart.data.labels = labels;
            multiCityChart.data.datasets = datasets;
            multiCityChart.update();
            syncUrlState();
        }

        // Update metric for multi-city chart
        const multiMetricEl = document.getElementById('multiCityMetric');
        if (multiMetricEl) multiMetricEl.value = multiCityMetric;
        document.getElementById('multiCityMetric').addEventListener('change', function(e) {
            multiCityMetric = e.target.value;
            if (!multiMetricOptions.includes(multiCityMetric)) multiCityMetric = 'inventory';
            setStoredValue('mc_metric', multiCityMetric);
            updateMultiCityChart();
            syncUrlState();
        });

        const metroOverlayEl = document.getElementById('multiCityMetro');
        const storedMetroOverlay = getStoredValue('mc_metro_overlay') === '1';
        const metroOverlayInitial = hasMetroOverlayParam ? initialMetroOverlayFromUrl : storedMetroOverlay;
        if (metroOverlayEl) {
            metroOverlayEl.checked = metroOverlayInitial;
            metroOverlayEl.addEventListener('change', function(e) {
                setStoredValue('mc_metro_overlay', e.target.checked ? '1' : '0');
                updateMultiCityChart();
                syncUrlState();
            });
        }

        // Bulk selection helpers
        function currentValueForCity(city, metric) {
            const series = (fullCityTrends[city] || cityTrends[city] || []);
            if (!series.length) return null;
            // Prefer the data point for the current period, else last point
            const exact = series.find(t => t.period === currentPeriod);
            const t = exact || series[series.length - 1];
            if (!t) return null;
            if (metric === 'sales') return t.homes_sold ?? null;
            if (metric === 'mos') {
                const inv = t.inventory, sold = t.homes_sold;
                return (inv && sold) ? inv / sold : null;
            }
            return null;
        }

        function bulkSelectTop(metricKey) {
            // metricKey: 'sales' or 'mos'
            const scored = availableCities.map(c => ({
                city: c,
                val: currentValueForCity(c, metricKey)
            })).filter(o => o.val !== null);
            if (!scored.length) return;
            // Sort desc for both (higher sales better, higher MoS indicates more supply)
            scored.sort((a,b) => b.val - a.val);
            const top = scored.slice(0, 5).map(o => o.city);

            // Clear all
            document.querySelectorAll('#cityCheckboxList input[type="checkbox"]').forEach(cb => cb.checked = false);
            selectedCities = [];
            // Check top
            top.forEach(c => {
                const input = [...document.querySelectorAll('#cityCheckboxList input[type="checkbox"]')].find(el => el.value === c);
                if (input) { input.checked = true; selectedCities.push(c); }
            });
            updateSelectedCitiesList();
            updateMultiCityChart();
            setStoredValue('mc_selected_cities', JSON.stringify(selectedCities));
            syncUrlState();
        }

        document.getElementById('btnTopSales').addEventListener('click', function(e){ e.preventDefault(); bulkSelectTop('sales'); });
        document.getElementById('btnTopSupply').addEventListener('click', function(e){ e.preventDefault(); bulkSelectTop('mos'); });
        document.getElementById('btnClearSel').addEventListener('click', function(e){
            e.preventDefault();
            document.querySelectorAll('#cityCheckboxList input[type="checkbox"]').forEach(cb => cb.checked = false);
            selectedCities = [];
            updateSelectedCitiesList();
            updateMultiCityChart();
            setStoredValue('mc_selected_cities', JSON.stringify(selectedCities));
            syncUrlState();
        });

        // Restore previously selected cities from localStorage
        function restoreMultiCitySelection() {
            const inputs = document.querySelectorAll('#cityCheckboxList input[type="checkbox"]');
            inputs.forEach(cb => {
                cb.checked = selectedCities.includes(cb.value);
            });
            updateSelectedCitiesList();
            updateMultiCityChart();
            setStoredValue('mc_selected_cities', JSON.stringify(selectedCities));
            syncUrlState();
        }

        // Reset all saved UI state
        document.getElementById('btnResetState').addEventListener('click', function(e){
            e.preventDefault();
            try {
                ['date_range','cityChartCity','cityChartMetric','mc_metric','mc_selected_cities','mc_metro_overlay'].forEach(k => removeStoredValue(k));
            } catch (e) {}
            // Reset selections
            if (citySelectEl) citySelectEl.value = cityNames[0];
            if (metricSelectEl) metricSelectEl.value = 'all';
            currentCity = cityNames[0];
            currentCityMetricMode = 'all';
            setStoredValue('cityChartCity', currentCity);
            setStoredValue('cityChartMetric', currentCityMetricMode);
            updateCityToggleState();
            updateCityChart();
            setCityRange('24m', document.querySelector('[data-city-range="24m"]'));

            selectedCities = [];
            document.querySelectorAll('#cityCheckboxList input[type="checkbox"]').forEach(cb => cb.checked = false);
            updateSelectedCitiesList();
            updateMultiCityChart();
            setStoredValue('mc_selected_cities', JSON.stringify(selectedCities));
            multiCityMetric = 'inventory';
            if (multiMetricEl) multiMetricEl.value = 'inventory';
            setStoredValue('mc_metric', multiCityMetric);
            if (metroOverlayEl) {
                metroOverlayEl.checked = false;
                setStoredValue('mc_metro_overlay', '0');
            }
            setDateRange('12m', document.querySelector('[data-range="12m"]'));
            syncUrlState();
        });

        // ============= EXPORT FUNCTIONS =============

        // Download chart as PNG image
        function downloadChartImage(chartId, filename) {
            const chartElement = document.getElementById(chartId);
            const url = chartElement.toDataURL('image/png');
            const link = document.createElement('a');
            link.download = filename + '_' + currentPeriod + '.png';
            link.href = url;
            link.click();
        }

        // Export chart data to CSV
        function exportChartCSV(chartId, filename) {
            const chart = Chart.getChart(chartId);
            if (!chart) return;

            const labels = chart.data.labels;
            const datasets = chart.data.datasets;

            // Build CSV content
            let csv = 'Period';
            datasets.forEach(ds => {
                csv += ',' + ds.label.replace(/,/g, ' ');
            });
            csv += '\\n';

            // Add data rows
            labels.forEach((label, i) => {
                csv += label;
                datasets.forEach(ds => {
                    const value = ds.data[i];
                    csv += ',' + (value !== null && value !== undefined ? value : '');
                });
                csv += '\\n';
            });

            // Download CSV file
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = filename + '_' + currentPeriod + '.csv';
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
        }

        // Initialize
        generateCityCheckboxes();
        restoreMultiCitySelection();
    </script>
</body>
</html>'''

    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Generated: {output_file}")

def main():
    """Generate dashboards for both metros"""

    base_dir = Path(__file__).parent

    # Charlotte
    generate_enhanced_dashboard(
        data_file=str(base_dir / 'charlotte' / '2025-09' / 'charlotte_data.json'),
        output_file=str(base_dir / 'charlotte' / '2025-09' / 'dashboard_enhanced_charlotte_2025-09.html')
    )

    # Roanoke
    generate_enhanced_dashboard(
        data_file=str(base_dir / 'roanoke' / '2025-09' / 'roanoke_data.json'),
        output_file=str(base_dir / 'roanoke' / '2025-09' / 'dashboard_enhanced_roanoke_2025-09.html')
    )

    print("\n[OK] All enhanced dashboards generated!")

if __name__ == '__main__':
    main()
