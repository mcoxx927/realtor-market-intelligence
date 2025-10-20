import pandas as pd
import json
import os

def generate_dashboard_html(market_name, dashboard_data):
    """Generate interactive HTML dashboard"""

    market_short = market_name.split(',')[0]
    market_filename = market_name.split(',')[0].lower().replace('-', '_').replace(' ', '_')

    current = dashboard_data['current_metrics']
    health_score = dashboard_data['health_score']
    sentiment = dashboard_data['sentiment']

    # Prepare historical data for charts (last 12 months)
    historical = sorted(dashboard_data['historical_data'], key=lambda x: x['month_date_yyyymm'])[-12:]

    # Generate JavaScript data
    chart_labels = [str(h['month_date_yyyymm']) for h in historical]
    chart_labels_formatted = []
    for label in chart_labels:
        year = label[:4]
        month = label[4:6]
        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        chart_labels_formatted.append(f"{month_names[int(month)]} {year}")

    active_listings = [h['active_listing_count'] for h in historical]
    new_listings = [h['new_listing_count'] for h in historical]
    pending_listings = [h['pending_listing_count'] for h in historical]
    median_prices = [h['median_listing_price'] for h in historical]
    days_on_market = [h['median_days_on_market'] for h in historical]
    pending_ratios = [h['pending_ratio'] for h in historical]
    price_reductions = [h['price_reduced_count'] for h in historical]
    price_increases = [h['price_increased_count'] for h in historical]

    # Determine color scheme based on sentiment
    if sentiment == "BULLISH":
        primary_color = "#10b981"
        sentiment_bg = "#064e3b"
    elif sentiment == "BEARISH":
        primary_color = "#ef4444"
        sentiment_bg = "#7f1d1d"
    else:
        primary_color = "#f59e0b"
        sentiment_bg = "#78350f"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{market_short} Real Estate Market Dashboard - September 2025</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        .card {{
            background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .health-score {{
            background: linear-gradient(135deg, {sentiment_bg} 0%, rgba(0, 0, 0, 0.4) 100%);
            border: 2px solid {primary_color};
        }}
        .trend-up {{
            color: #10b981;
        }}
        .trend-down {{
            color: #ef4444;
        }}
        .trend-neutral {{
            color: #6b7280;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .animate-in {{
            animation: fadeIn 0.6s ease-out forwards;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">

        <!-- Header -->
        <div class="card rounded-2xl p-6 md:p-8 animate-in">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 class="text-3xl md:text-4xl font-bold text-white mb-2">{market_short} Market Intelligence</h1>
                    <p class="text-gray-400 text-lg">September 2025 Market Analysis</p>
                </div>
                <div class="health-score rounded-xl p-6 text-center">
                    <div class="text-sm text-gray-300 mb-2">Market Health Score</div>
                    <div class="text-5xl font-bold" style="color: {primary_color};">{health_score}</div>
                    <div class="text-xl font-semibold mt-2" style="color: {primary_color};">{sentiment}</div>
                </div>
            </div>
        </div>

        <!-- Key Metrics Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- Median Price -->
            <div class="card rounded-xl p-6 animate-in">
                <div class="text-gray-400 text-sm mb-2">Median Listing Price</div>
                <div class="text-3xl font-bold text-white mb-2">${current['median_listing_price']:,.0f}</div>
                <div class="flex items-center gap-2 text-sm">
                    <span class="{'trend-up' if current['median_listing_price_mm'] > 0 else 'trend-down' if current['median_listing_price_mm'] < 0 else 'trend-neutral'}">
                        {'+' if current['median_listing_price_mm'] > 0 else ''}{current['median_listing_price_mm']:.1f}% MoM
                    </span>
                    <span class="text-gray-500">|</span>
                    <span class="{'trend-up' if current['median_listing_price_yy'] > 0 else 'trend-down' if current['median_listing_price_yy'] < 0 else 'trend-neutral'}">
                        {'+' if current['median_listing_price_yy'] > 0 else ''}{current['median_listing_price_yy']:.1f}% YoY
                    </span>
                </div>
            </div>

            <!-- Active Listings -->
            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.1s;">
                <div class="text-gray-400 text-sm mb-2">Active Listings</div>
                <div class="text-3xl font-bold text-white mb-2">{current['active_listing_count']:,}</div>
                <div class="flex items-center gap-2 text-sm">
                    <span class="{'trend-up' if current['active_listing_count_mm'] > 0 else 'trend-down' if current['active_listing_count_mm'] < 0 else 'trend-neutral'}">
                        {'+' if current['active_listing_count_mm'] > 0 else ''}{current['active_listing_count_mm']:.1f}% MoM
                    </span>
                    <span class="text-gray-500">|</span>
                    <span class="{'trend-up' if current['active_listing_count_yy'] > 0 else 'trend-down' if current['active_listing_count_yy'] < 0 else 'trend-neutral'}">
                        {'+' if current['active_listing_count_yy'] > 0 else ''}{current['active_listing_count_yy']:.1f}% YoY
                    </span>
                </div>
            </div>

            <!-- Days on Market -->
            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.2s;">
                <div class="text-gray-400 text-sm mb-2">Days on Market</div>
                <div class="text-3xl font-bold text-white mb-2">{current['median_days_on_market']} days</div>
                <div class="flex items-center gap-2 text-sm">
                    <span class="{'trend-down' if current['median_days_on_market_mm'] > 0 else 'trend-up' if current['median_days_on_market_mm'] < 0 else 'trend-neutral'}">
                        {'+' if current['median_days_on_market_mm'] > 0 else ''}{current['median_days_on_market_mm']:.1f}% MoM
                    </span>
                    <span class="text-gray-500">|</span>
                    <span class="{'trend-down' if current['median_days_on_market_yy'] > 0 else 'trend-up' if current['median_days_on_market_yy'] < 0 else 'trend-neutral'}">
                        {'+' if current['median_days_on_market_yy'] > 0 else ''}{current['median_days_on_market_yy']:.1f}% YoY
                    </span>
                </div>
            </div>

            <!-- Pending Ratio -->
            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.3s;">
                <div class="text-gray-400 text-sm mb-2">Pending Ratio</div>
                <div class="text-3xl font-bold text-white mb-2">{current['pending_ratio']:.3f}</div>
                <div class="flex items-center gap-2 text-sm">
                    <span class="{'trend-up' if current['pending_ratio_mm'] > 0 else 'trend-down' if current['pending_ratio_mm'] < 0 else 'trend-neutral'}">
                        {'+' if current['pending_ratio_mm'] > 0 else ''}{current['pending_ratio_mm']:.1f}% MoM
                    </span>
                    <span class="text-gray-500">|</span>
                    <span class="{'trend-up' if current['pending_ratio_yy'] > 0 else 'trend-down' if current['pending_ratio_yy'] < 0 else 'trend-neutral'}">
                        {'+' if current['pending_ratio_yy'] > 0 else ''}{current['pending_ratio_yy']:.1f}% YoY
                    </span>
                </div>
            </div>
        </div>

        <!-- Executive Summary -->
        <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.4s;">
            <h2 class="text-2xl font-bold text-white mb-4">Executive Summary</h2>
            <div class="space-y-3 text-gray-300">
                <div class="flex items-start gap-3">
                    <span class="text-2xl">&#8226;</span>
                    <span>Market conditions are <strong style="color: {primary_color};">{sentiment}</strong> with a health score of {health_score}/100, indicating {'strong fundamentals and favorable conditions' if health_score >= 70 else 'balanced market dynamics with moderate activity' if health_score >= 50 else 'softening conditions requiring strategic approach'}.</span>
                </div>
                <div class="flex items-start gap-3">
                    <span class="text-2xl">&#8226;</span>
                    <span>Inventory levels {'increased significantly' if current['active_listing_count_mm'] > 10 else 'grew moderately' if current['active_listing_count_mm'] > 5 else 'remained relatively stable' if abs(current['active_listing_count_mm']) <= 5 else 'declined'} with {current['active_listing_count']:,} active listings, up {current['active_listing_count_yy']:.1f}% year-over-year.</span>
                </div>
                <div class="flex items-start gap-3">
                    <span class="text-2xl">&#8226;</span>
                    <span>Sales velocity shows homes selling in {current['median_days_on_market']} days on average, {'indicating strong buyer demand' if current['median_days_on_market'] < 45 else 'reflecting balanced market conditions' if current['median_days_on_market'] < 60 else 'suggesting softer demand dynamics'}.</span>
                </div>
                <div class="flex items-start gap-3">
                    <span class="text-2xl">&#8226;</span>
                    <span>Pricing power {'remains strong' if current['price_reduced_count'] / current['active_listing_count'] < 0.35 else 'is balanced' if current['price_reduced_count'] / current['active_listing_count'] < 0.45 else 'has shifted to buyers'} with {current['price_reduced_count']:,} price reductions ({(current['price_reduced_count'] / current['active_listing_count'] * 100):.1f}% of inventory).</span>
                </div>
            </div>
        </div>

        <!-- Inventory Dynamics Chart -->
        <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.5s;">
            <h2 class="text-2xl font-bold text-white mb-4">Inventory Dynamics (Last 12 Months)</h2>
            <div class="chart-container">
                <canvas id="inventoryChart"></canvas>
            </div>
        </div>

        <!-- Pricing Analysis -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.6s;">
                <h2 class="text-2xl font-bold text-white mb-4">Median Price Trend</h2>
                <div class="chart-container">
                    <canvas id="priceChart"></canvas>
                </div>
            </div>

            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.7s;">
                <h2 class="text-2xl font-bold text-white mb-4">Price Adjustments</h2>
                <div class="chart-container">
                    <canvas id="priceAdjustmentChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Market Velocity -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.8s;">
                <h2 class="text-2xl font-bold text-white mb-4">Days on Market Trend</h2>
                <div class="chart-container">
                    <canvas id="domChart"></canvas>
                </div>
            </div>

            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 0.9s;">
                <h2 class="text-2xl font-bold text-white mb-4">Pending Ratio Trend</h2>
                <div class="chart-container">
                    <canvas id="pendingRatioChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Additional Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 1.0s;">
                <div class="text-gray-400 text-sm mb-2">New Listings</div>
                <div class="text-2xl font-bold text-white mb-2">{current['new_listing_count']:,}</div>
                <div class="text-sm {'trend-up' if current['new_listing_count_mm'] > 0 else 'trend-down' if current['new_listing_count_mm'] < 0 else 'trend-neutral'}">
                    {'+' if current['new_listing_count_mm'] > 0 else ''}{current['new_listing_count_mm']:.1f}% from last month
                </div>
            </div>

            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 1.1s;">
                <div class="text-gray-400 text-sm mb-2">Price Reductions</div>
                <div class="text-2xl font-bold text-white mb-2">{current['price_reduced_count']:,}</div>
                <div class="text-sm text-gray-400">
                    {(current['price_reduced_count'] / current['active_listing_count'] * 100):.1f}% of active inventory
                </div>
            </div>

            <div class="card rounded-xl p-6 animate-in" style="animation-delay: 1.2s;">
                <div class="text-gray-400 text-sm mb-2">Price per Sq Ft</div>
                <div class="text-2xl font-bold text-white mb-2">${current['median_price_per_sqft']:,}</div>
                <div class="text-sm text-gray-400">
                    Median pricing metric
                </div>
            </div>
        </div>

        <!-- Predictive Insights -->
        <div class="card rounded-xl p-6 animate-in" style="animation-delay: 1.3s;">
            <h2 class="text-2xl font-bold text-white mb-4">Market Direction Indicator</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="metric-card rounded-lg p-4">
                    <div class="text-gray-400 text-sm mb-2">Market Direction</div>
                    <div class="text-xl font-bold" style="color: {primary_color};">
                        {'Heating Up' if health_score >= 70 else 'Stable' if health_score >= 50 else 'Cooling'}
                    </div>
                </div>
                <div class="metric-card rounded-lg p-4">
                    <div class="text-gray-400 text-sm mb-2">Momentum Score</div>
                    <div class="text-xl font-bold text-white">
                        {health_score}/100
                    </div>
                </div>
                <div class="metric-card rounded-lg p-4">
                    <div class="text-gray-400 text-sm mb-2">Key Driver</div>
                    <div class="text-xl font-bold text-white">
                        {'Supply Growth' if current['active_listing_count_yy'] > 20 else 'Pricing' if abs(current['median_listing_price_mm']) > 2 else 'Demand Shift' if abs(current['pending_ratio_mm']) > 5 else 'Balanced'}
                    </div>
                </div>
            </div>
            <div class="mt-4 p-4 bg-blue-900 bg-opacity-30 rounded-lg">
                <div class="text-white font-semibold mb-2">Watch Items for Next Month:</div>
                <ul class="text-gray-300 space-y-1 text-sm">
                    <li>&#8226; Monitor price reduction rates for signs of increasing seller pressure</li>
                    <li>&#8226; Track new listing velocity as indicator of seller confidence</li>
                    <li>&#8226; Watch pending ratio changes for early demand signals</li>
                    <li>&#8226; Observe days on market trend for market absorption capacity</li>
                </ul>
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center text-gray-500 text-sm pb-4">
            Report generated on October 15, 2025 | Data source: Realtor.com | Analysis period: September 2025
        </div>

    </div>

    <script>
        Chart.defaults.color = '#9ca3af';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    labels: {{
                        color: '#e5e7eb',
                        font: {{ size: 12 }}
                    }}
                }},
                tooltip: {{
                    backgroundColor: 'rgba(15, 52, 96, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#e5e7eb',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1
                }}
            }},
            scales: {{
                y: {{
                    grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                    ticks: {{ color: '#9ca3af' }}
                }},
                x: {{
                    grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                    ticks: {{ color: '#9ca3af' }}
                }}
            }}
        }};

        // Inventory Chart
        new Chart(document.getElementById('inventoryChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_labels_formatted)},
                datasets: [
                    {{
                        label: 'Active Listings',
                        data: {json.dumps(active_listings)},
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: 'New Listings',
                        data: {json.dumps(new_listings)},
                        borderColor: '#10b981',
                        tension: 0.4
                    }},
                    {{
                        label: 'Pending Listings',
                        data: {json.dumps(pending_listings)},
                        borderColor: '#f59e0b',
                        tension: 0.4
                    }}
                ]
            }},
            options: chartOptions
        }});

        // Price Chart
        new Chart(document.getElementById('priceChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_labels_formatted)},
                datasets: [{{
                    label: 'Median Listing Price',
                    data: {json.dumps(median_prices)},
                    borderColor: '{primary_color}',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    ...chartOptions.scales,
                    y: {{
                        ...chartOptions.scales.y,
                        ticks: {{
                            color: '#9ca3af',
                            callback: function(value) {{
                                return '$' + value.toLocaleString();
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Price Adjustment Chart
        new Chart(document.getElementById('priceAdjustmentChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_labels_formatted)},
                datasets: [
                    {{
                        label: 'Price Reductions',
                        data: {json.dumps(price_reductions)},
                        backgroundColor: '#ef4444'
                    }},
                    {{
                        label: 'Price Increases',
                        data: {json.dumps(price_increases)},
                        backgroundColor: '#10b981'
                    }}
                ]
            }},
            options: chartOptions
        }});

        // Days on Market Chart
        new Chart(document.getElementById('domChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_labels_formatted)},
                datasets: [{{
                    label: 'Days on Market',
                    data: {json.dumps(days_on_market)},
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: chartOptions
        }});

        // Pending Ratio Chart
        new Chart(document.getElementById('pendingRatioChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_labels_formatted)},
                datasets: [{{
                    label: 'Pending Ratio',
                    data: {json.dumps(pending_ratios)},
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: chartOptions
        }});
    </script>
</body>
</html>"""

    return html

# Main execution
if __name__ == "__main__":
    markets = [
        ('Charlotte-Concord-Gastonia, NC-SC', 'charlotte/2025-09'),
        ('Roanoke, VA', 'roanoke/2025-09')
    ]

    for market_name, output_dir in markets:
        market_short = market_name.split(',')[0].lower().replace('-', '_').replace(' ', '_')

        print(f"\nGenerating dashboard for {market_name}...")

        # Load dashboard data
        with open(os.path.join(output_dir, 'dashboard_data.json'), 'r') as f:
            dashboard_data = json.load(f)

        # Generate HTML
        html = generate_dashboard_html(market_name, dashboard_data)

        # Save HTML
        html_filename = f"dashboard_{market_short}_2025-09.html"
        with open(os.path.join(output_dir, html_filename), 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  - Created {html_filename}")

    print("\nAll dashboards generated successfully!")
