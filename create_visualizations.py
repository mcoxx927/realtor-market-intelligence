import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Read data
file_path = r"C:\Users\1\Documents\GitHub\realtor monthly data analysis\Realtor New Listings.xlsx"
df = pd.read_excel(file_path, sheet_name='RDC_Inventory_Core_Metrics_Metr')

# Convert date
df['date'] = pd.to_datetime(df['month_date_yyyymm'].astype(str), format='%Y%m')
df = df.sort_values('date')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
fig = plt.figure(figsize=(20, 24))

# Markets
markets = df['cbsa_title'].unique()
colors = {'Charlotte-Concord-Gastonia, NC-SC': '#1f77b4', 'Roanoke, VA': '#ff7f0e'}

# Plot 1: Median Listing Price Trend
ax1 = plt.subplot(6, 2, 1)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax1.plot(market_data['date'], market_data['median_listing_price'],
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax1.set_title('Median Listing Price Trend', fontsize=14, fontweight='bold')
ax1.set_ylabel('Price ($)', fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 2: Active Inventory Trend
ax2 = plt.subplot(6, 2, 2)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax2.plot(market_data['date'], market_data['active_listing_count'],
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax2.set_title('Active Inventory Trend', fontsize=14, fontweight='bold')
ax2.set_ylabel('Active Listings', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 3: Days on Market Trend
ax3 = plt.subplot(6, 2, 3)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax3.plot(market_data['date'], market_data['median_days_on_market'],
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax3.set_title('Median Days on Market', fontsize=14, fontweight='bold')
ax3.set_ylabel('Days', fontsize=12)
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 4: Pending Ratio Trend
ax4 = plt.subplot(6, 2, 4)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax4.plot(market_data['date'], market_data['pending_ratio'],
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax4.set_title('Pending Ratio (Demand Indicator)', fontsize=14, fontweight='bold')
ax4.set_ylabel('Ratio', fontsize=12)
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)
ax4.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Balanced Market')
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 5: New Listings Trend
ax5 = plt.subplot(6, 2, 5)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax5.plot(market_data['date'], market_data['new_listing_count'],
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax5.set_title('New Listings Per Month', fontsize=14, fontweight='bold')
ax5.set_ylabel('Count', fontsize=12)
ax5.legend(fontsize=10)
ax5.grid(True, alpha=0.3)
plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 6: Price Per Square Foot
ax6 = plt.subplot(6, 2, 6)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax6.plot(market_data['date'], market_data['median_listing_price_per_square_foot'],
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax6.set_title('Price Per Square Foot', fontsize=14, fontweight='bold')
ax6.set_ylabel('$/Sq Ft', fontsize=12)
ax6.legend(fontsize=10)
ax6.grid(True, alpha=0.3)
plt.setp(ax6.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 7: Price Reductions
ax7 = plt.subplot(6, 2, 7)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax7.plot(market_data['date'], market_data['price_reduced_count'],
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax7.set_title('Price Reductions Count', fontsize=14, fontweight='bold')
ax7.set_ylabel('Count', fontsize=12)
ax7.legend(fontsize=10)
ax7.grid(True, alpha=0.3)
plt.setp(ax7.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 8: Price Reduction Ratio
ax8 = plt.subplot(6, 2, 8)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    reduction_ratio = (market_data['price_reduced_count'] / market_data['active_listing_count']) * 100
    ax8.plot(market_data['date'], reduction_ratio,
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax8.set_title('Price Reduction Ratio (% of Active Inventory)', fontsize=14, fontweight='bold')
ax8.set_ylabel('Percentage', fontsize=12)
ax8.legend(fontsize=10)
ax8.grid(True, alpha=0.3)
ax8.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50% Threshold')
plt.setp(ax8.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 9: YoY Price Change
ax9 = plt.subplot(6, 2, 9)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    yoy_change = market_data['median_listing_price_yy'] * 100
    ax9.plot(market_data['date'], yoy_change,
             label=market, linewidth=2, color=colors.get(market, 'gray'))
ax9.set_title('YoY Median Price Change (%)', fontsize=14, fontweight='bold')
ax9.set_ylabel('Percent Change', fontsize=12)
ax9.legend(fontsize=10)
ax9.grid(True, alpha=0.3)
ax9.axhline(y=0, color='red', linestyle='-', alpha=0.5)
plt.setp(ax9.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 10: YoY Inventory Change
ax10 = plt.subplot(6, 2, 10)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    yoy_inv_change = market_data['active_listing_count_yy'] * 100
    ax10.plot(market_data['date'], yoy_inv_change,
              label=market, linewidth=2, color=colors.get(market, 'gray'))
ax10.set_title('YoY Active Inventory Change (%)', fontsize=14, fontweight='bold')
ax10.set_ylabel('Percent Change', fontsize=12)
ax10.legend(fontsize=10)
ax10.grid(True, alpha=0.3)
ax10.axhline(y=0, color='red', linestyle='-', alpha=0.5)
plt.setp(ax10.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 11: Total Listings
ax11 = plt.subplot(6, 2, 11)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax11.plot(market_data['date'], market_data['total_listing_count'],
              label=market, linewidth=2, color=colors.get(market, 'gray'))
ax11.set_title('Total Listings (Active + Pending)', fontsize=14, fontweight='bold')
ax11.set_ylabel('Count', fontsize=12)
ax11.legend(fontsize=10)
ax11.grid(True, alpha=0.3)
plt.setp(ax11.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 12: Median Square Feet
ax12 = plt.subplot(6, 2, 12)
for market in markets:
    market_data = df[df['cbsa_title'] == market]
    ax12.plot(market_data['date'], market_data['median_square_feet'],
              label=market, linewidth=2, color=colors.get(market, 'gray'))
ax12.set_title('Median Square Feet', fontsize=14, fontweight='bold')
ax12.set_ylabel('Square Feet', fontsize=12)
ax12.legend(fontsize=10)
ax12.grid(True, alpha=0.3)
plt.setp(ax12.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig(r'C:\Users\1\Documents\GitHub\realtor monthly data analysis\market_analysis_charts.png',
            dpi=300, bbox_inches='tight')
print("Comprehensive visualization saved to: market_analysis_charts.png")

# Create comparison charts for latest month
fig2, axes = plt.subplots(2, 3, figsize=(18, 12))
fig2.suptitle('September 2025 Market Comparison', fontsize=16, fontweight='bold')

latest_data = df[df['date'] == df['date'].max()]

# Chart 1: Median Price
ax1 = axes[0, 0]
bars1 = ax1.bar(range(len(markets)), [latest_data[latest_data['cbsa_title']==m]['median_listing_price'].values[0] for m in markets],
                color=[colors.get(m, 'gray') for m in markets])
ax1.set_title('Median Listing Price', fontweight='bold')
ax1.set_ylabel('Price ($)')
ax1.set_xticks(range(len(markets)))
ax1.set_xticklabels([m.split(',')[0] for m in markets], rotation=45, ha='right')
for i, bar in enumerate(bars1):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'${height:,.0f}', ha='center', va='bottom')

# Chart 2: Active Listings
ax2 = axes[0, 1]
bars2 = ax2.bar(range(len(markets)), [latest_data[latest_data['cbsa_title']==m]['active_listing_count'].values[0] for m in markets],
                color=[colors.get(m, 'gray') for m in markets])
ax2.set_title('Active Listings', fontweight='bold')
ax2.set_ylabel('Count')
ax2.set_xticks(range(len(markets)))
ax2.set_xticklabels([m.split(',')[0] for m in markets], rotation=45, ha='right')
for i, bar in enumerate(bars2):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:,.0f}', ha='center', va='bottom')

# Chart 3: Days on Market
ax3 = axes[0, 2]
bars3 = ax3.bar(range(len(markets)), [latest_data[latest_data['cbsa_title']==m]['median_days_on_market'].values[0] for m in markets],
                color=[colors.get(m, 'gray') for m in markets])
ax3.set_title('Median Days on Market', fontweight='bold')
ax3.set_ylabel('Days')
ax3.set_xticks(range(len(markets)))
ax3.set_xticklabels([m.split(',')[0] for m in markets], rotation=45, ha='right')
for i, bar in enumerate(bars3):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)}', ha='center', va='bottom')

# Chart 4: Pending Ratio
ax4 = axes[1, 0]
bars4 = ax4.bar(range(len(markets)), [latest_data[latest_data['cbsa_title']==m]['pending_ratio'].values[0] for m in markets],
                color=[colors.get(m, 'gray') for m in markets])
ax4.set_title('Pending Ratio', fontweight='bold')
ax4.set_ylabel('Ratio')
ax4.set_xticks(range(len(markets)))
ax4.set_xticklabels([m.split(',')[0] for m in markets], rotation=45, ha='right')
ax4.axhline(y=0.5, color='red', linestyle='--', alpha=0.5)
for i, bar in enumerate(bars4):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.3f}', ha='center', va='bottom')

# Chart 5: Price Reduction %
ax5 = axes[1, 1]
reduction_pcts = [(latest_data[latest_data['cbsa_title']==m]['price_reduced_count'].values[0] /
                   latest_data[latest_data['cbsa_title']==m]['active_listing_count'].values[0] * 100) for m in markets]
bars5 = ax5.bar(range(len(markets)), reduction_pcts,
                color=[colors.get(m, 'gray') for m in markets])
ax5.set_title('Price Reduction Rate', fontweight='bold')
ax5.set_ylabel('% of Active Inventory')
ax5.set_xticks(range(len(markets)))
ax5.set_xticklabels([m.split(',')[0] for m in markets], rotation=45, ha='right')
ax5.axhline(y=50, color='red', linestyle='--', alpha=0.5)
for i, bar in enumerate(bars5):
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.1f}%', ha='center', va='bottom')

# Chart 6: YoY Price Change
ax6 = axes[1, 2]
yoy_changes = [latest_data[latest_data['cbsa_title']==m]['median_listing_price_yy'].values[0] * 100 for m in markets]
bar_colors = ['green' if x > 0 else 'red' for x in yoy_changes]
bars6 = ax6.bar(range(len(markets)), yoy_changes, color=bar_colors, alpha=0.7)
ax6.set_title('YoY Price Change', fontweight='bold')
ax6.set_ylabel('% Change')
ax6.set_xticks(range(len(markets)))
ax6.set_xticklabels([m.split(',')[0] for m in markets], rotation=45, ha='right')
ax6.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
for i, bar in enumerate(bars6):
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:+.1f}%', ha='center', va='bottom' if height > 0 else 'top')

plt.tight_layout()
plt.savefig(r'C:\Users\1\Documents\GitHub\realtor monthly data analysis\september_2025_comparison.png',
            dpi=300, bbox_inches='tight')
print("September 2025 comparison saved to: september_2025_comparison.png")

print("\nVisualization generation complete!")
