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

    # City selector options (top 5)
    city_names = list(city_trends.keys())

    # Build city dropdown options
    city_options = '\n'.join([f'<option value="{city}">{city}</option>' for city in city_names])

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
                <div class="flex flex-wrap gap-2">
                    <button data-range="6m" onclick="setDateRange('6m', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">Last 6 Months</button>
                    <button data-range="12m" onclick="setDateRange('12m', this)" class="px-4 py-2 bg-blue-500/40 border-2 border-blue-500 rounded-lg text-sm font-bold">Last 12 Months</button>
                    <button data-range="ytd" onclick="setDateRange('ytd', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">YTD 2025</button>
                    <button data-range="2y" onclick="setDateRange('2y', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">Last 2 Years</button>
                    <button data-range="5y" onclick="setDateRange('5y', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">Last 5 Years</button>
                    <button data-range="all" onclick="setDateRange('all', this)" class="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/40 border border-blue-500/50 rounded-lg transition text-sm font-medium">All Time</button>
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

        <!-- Top 5 Cities Comparison (Single City View) -->
        <div class="card p-6 text-white">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-2xl font-bold">Top 5 Cities Historical Trends</h2>
                <div class="flex gap-2">
                    <select id="citySelector" class="selector">
                        {city_options}
                    </select>
                    <select id="cityMetric" class="selector">
                        <option value="inventory">Inventory</option>
                        <option value="sales">Homes Sold</option>
                        <option value="dom">Days on Market</option>
                        <option value="price">Median Price</option>
                    </select>
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
                    <div class="bg-white/5 border border-white/20 rounded-lg max-h-48 overflow-y-auto p-2" id="cityCheckboxList">
                        <!-- Checkboxes will be generated by JavaScript -->
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

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#e5e7eb' } },
                tooltip: {
                    backgroundColor: 'rgba(15, 52, 96, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#e5e7eb'
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

        // Data (12-month embedded for fast initial load)
        const labels = ''' + labels_json + ''';
        const defaultPeriods = ''' + periods_json + ''';
        const inventoryData = ''' + inventory_json + ''';
        const newListingsData = ''' + new_listings_json + ''';
        const pendingData = ''' + pending_json + ''';
        const priceDropsData = ''' + price_drops_json + ''';
        const domData = ''' + dom_json + ''';
        const pendingRatioData = ''' + pending_ratio_json + ''';
        const homesSoldData = ''' + homes_sold_json + ''';
        const medianPriceData = ''' + median_price_json + ''';
        const currentPeriod = ''' + period_json + ''';

        // City trends data (12-month default, top 5 cities)
        const cityTrends = ''' + city_trends_json + ''';
        const fullMetroTrends = ''' + full_metro_trends_json + ''';
        const fullCityTrends = ''' + full_city_trends_json + ''';
        const availableCities = ''' + available_cities_json + ''';

        // Current date range state
        let currentRange = '12m';
        let filteredMetroData = null;

        // Format period labels helper
        function formatLabels(periods) {
            return periods.map(period => {
                const [year, month] = period.split('-');
                const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                return monthNames[parseInt(month)] + " '" + year.slice(2);
            });
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
                pending_ratio: pendingRatioData.slice()
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
                pending_ratio: effective.map(t => t.pending_ratio || 0)
            };
        }

        // Initialize with 12 month default
        try {
            filteredMetroData = filterDataByRange('12m');
            console.log('Filtered data initialized:', filteredMetroData ? 'SUCCESS' : 'FAILED');
        } catch (e) {
            console.error('Error initializing filtered data:', e);
            alert('Error loading chart data: ' + e.message);
        }

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
                            tension: 0.4
                        },
                        {
                            label: 'New Listings',
                            data: filteredMetroData.new_listings,
                            borderColor: '#10b981',
                            tension: 0.4
                        },
                        {
                            label: 'Pending Sales',
                            data: filteredMetroData.pending_sales,
                            borderColor: '#f59e0b',
                            tension: 0.4
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
                    { label: 'Active Listings', data: filteredMetroData.inventory, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.4, borderWidth: 2 },
                    { label: 'New Listings', data: filteredMetroData.new_listings, borderColor: '#10b981', tension: 0.4, borderWidth: 2 },
                    { label: 'Pending Sales', data: filteredMetroData.pending_sales, borderColor: '#f59e0b', tension: 0.4, borderWidth: 2 }
                ];
            } else if (value === 'inventory') {
                datasets = [
                    { label: 'Active Listings', data: filteredMetroData.inventory, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.4, borderWidth: 2 }
                ];
            } else if (value === 'new_listings') {
                datasets = [
                    { label: 'New Listings', data: filteredMetroData.new_listings, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.4, borderWidth: 2 }
                ];
            } else if (value === 'pending') {
                datasets = [
                    { label: 'Pending Sales', data: filteredMetroData.pending_sales, borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', fill: true, tension: 0.4, borderWidth: 2 }
                ];
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
                    backgroundColor: '#ef4444'
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
                        tension: 0.4
                    },
                    {
                        label: 'Homes Sold (Demand)',
                        data: filteredMetroData.homes_sold,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4
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
                        yAxisID: 'y'
                    },
                    {
                        label: 'Pending Ratio',
                        data: filteredMetroData.pending_ratio,
                        borderColor: '#f59e0b',
                        tension: 0.4,
                        yAxisID: 'y1'
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

        // City Chart (Dynamic) - Show ONE metric at a time
        const firstCity = Object.keys(cityTrends)[0];
        const cityLabels = cityTrends[firstCity].map(t => {
            const [year, month] = t.period.split('-');
            const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return monthNames[parseInt(month)] + " '" + year.slice(2);
        });

        let currentCity = firstCity;
        let currentMetric = 'inventory';

        function getCityData(city, metric) {
            if (metric === 'inventory') {
                return cityTrends[city].map(t => t.inventory);
            } else if (metric === 'sales') {
                return cityTrends[city].map(t => t.homes_sold);
            } else if (metric === 'dom') {
                return cityTrends[city].map(t => t.median_dom);
            } else if (metric === 'price') {
                return cityTrends[city].map(t => t.median_sale_price);
            }
        }

        function getMetricLabel(metric) {
            if (metric === 'inventory') return 'Inventory';
            if (metric === 'sales') return 'Homes Sold';
            if (metric === 'dom') return 'Days on Market';
            if (metric === 'price') return 'Median Sale Price';
        }

        function getMetricColor(metric) {
            if (metric === 'inventory') return '#3b82f6';
            if (metric === 'sales') return '#10b981';
            if (metric === 'dom') return '#8b5cf6';
            if (metric === 'price') return '#f59e0b';
        }

        let cityChart = new Chart(document.getElementById('cityChart'), {
            type: 'line',
            data: {
                labels: cityLabels,
                datasets: [{
                    label: getMetricLabel(currentMetric),
                    data: getCityData(currentCity, currentMetric),
                    borderColor: getMetricColor(currentMetric),
                    backgroundColor: getMetricColor(currentMetric) + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: chartOptions
        });

        // Update city chart when city changes
        document.getElementById('citySelector').addEventListener('change', function(e) {
            currentCity = e.target.value;
            cityChart.data.datasets = [{
                label: getMetricLabel(currentMetric),
                data: getCityData(currentCity, currentMetric),
                borderColor: getMetricColor(currentMetric),
                backgroundColor: getMetricColor(currentMetric) + '20',
                fill: true,
                tension: 0.4
            }];
            cityChart.update();
        });

        // Update city chart when metric changes
        document.getElementById('cityMetric').addEventListener('change', function(e) {
            currentMetric = e.target.value;
            cityChart.data.datasets = [{
                label: getMetricLabel(currentMetric),
                data: getCityData(currentCity, currentMetric),
                borderColor: getMetricColor(currentMetric),
                backgroundColor: getMetricColor(currentMetric) + '20',
                fill: true,
                tension: 0.4
            }];
            cityChart.update();
        });

        // ============= MULTI-CITY COMPARISON TOOL =============

        // Generate distinct colors for cities
        const cityColors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
            '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16',
            '#a855f7', '#22c55e', '#eab308', '#6366f1', '#f43f5e',
            '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
        ];

        let selectedCities = [];
        let multiCityMetric = 'inventory';

        // Generate checkbox list
        function generateCityCheckboxes() {
            const container = document.getElementById('cityCheckboxList');
            container.innerHTML = '';

            availableCities.forEach((city, index) => {
                const div = document.createElement('div');
                div.className = 'flex items-center gap-2 p-2 hover:bg-white/5 rounded cursor-pointer';
                div.innerHTML = `
                    <input type="checkbox" id="city_$${index}" value="${city}"
                           class="city-checkbox w-4 h-4 cursor-pointer"
                           onchange="toggleCity(this)">
                    <label for="city_$${index}" class="cursor-pointer flex-1 text-sm">${city}</label>
                `;
                container.appendChild(div);
            });
        }

        // Toggle city selection
        function toggleCity(checkbox) {
            const city = checkbox.value;
            if (checkbox.checked) {
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
            const series = fullCityTrends[city] || cityTrends[city];
            if (!series) return [];

            if (metric === 'inventory') {
                return series.map(t => t.inventory);
            } else if (metric === 'sales') {
                return series.map(t => t.homes_sold);
            } else if (metric === 'dom') {
                return series.map(t => t.median_dom);
            } else if (metric === 'price') {
                return series.map(t => t.median_sale_price);
            }
        }

        // Get multi-city labels (use first city's periods)
        function getMultiCityLabels() {
            if (selectedCities.length === 0) return [];
            const firstCity = selectedCities[0];
            const series = fullCityTrends[firstCity] || cityTrends[firstCity];
            if (!series) return [];
            return formatLabels(series.map(t => t.period));
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
                return;
            }

            const labels = getMultiCityLabels();
            const datasets = [];

            // Add main city data
            selectedCities.forEach((city, i) => {
                const color = cityColors[i % cityColors.length];
                const cityData = getMultiCityData(city, multiCityMetric);

                datasets.push({
                    label: city,
                    data: cityData,
                    borderColor: color,
                    backgroundColor: color + '20',
                    tension: 0.4,
                    borderWidth: 2
                });

                // Add moving averages for each city if enabled
                if (document.getElementById('multiCityMA3').checked) {
                    datasets.push({
                        label: city + ' (3-Mo MA)',
                        data: calculateSMA(cityData, 3),
                        borderColor: color,
                        borderDash: [5, 5],
                        borderWidth: 1,
                        tension: 0.4,
                        pointRadius: 0
                    });
                }
                if (document.getElementById('multiCityMA6').checked) {
                    datasets.push({
                        label: city + ' (6-Mo MA)',
                        data: calculateSMA(cityData, 6),
                        borderColor: color,
                        borderDash: [8, 4],
                        borderWidth: 1,
                        tension: 0.4,
                        pointRadius: 0
                    });
                }
                if (document.getElementById('multiCityMA12').checked) {
                    datasets.push({
                        label: city + ' (12-Mo MA)',
                        data: calculateSMA(cityData, 12),
                        borderColor: color,
                        borderDash: [10, 3],
                        borderWidth: 1,
                        tension: 0.4,
                        pointRadius: 0
                    });
                }
                if (document.getElementById('multiCityTrend').checked) {
                    datasets.push({
                        label: city + ' (Trend)',
                        data: calculateTrendLine(cityData),
                        borderColor: color,
                        borderDash: [2, 2],
                        borderWidth: 1,
                        tension: 0,
                        pointRadius: 0
                    });
                }
            });

            multiCityChart.data.labels = labels;
            multiCityChart.data.datasets = datasets;
            multiCityChart.update();
        }

        // Update metric for multi-city chart
        document.getElementById('multiCityMetric').addEventListener('change', function(e) {
            multiCityMetric = e.target.value;
            updateMultiCityChart();
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
