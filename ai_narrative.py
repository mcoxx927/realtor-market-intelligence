"""
AI Market Narrative Generator
Uses Claude API to generate investor-ready market analysis narratives.

Usage:
    python ai_narrative.py                    # Generate for all metros
    python ai_narrative.py --metro charlotte  # Generate for specific metro
    python ai_narrative.py --preview          # Preview prompt without API call

Environment Variables:
    ANTHROPIC_API_KEY - Your Anthropic API key (or configure in notifications_config.json)
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Try to import anthropic, handle gracefully if not installed
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def load_config():
    """Load AI narrative configuration."""
    base_dir = Path(__file__).parent
    config_file = base_dir / 'notifications_config.json'

    config = {
        'enabled': False,
        'api_key': '',
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 2000,
        'generate_for_all_metros': True
    }

    # Load from config file if exists
    if config_file.exists():
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            if 'ai_narrative' in file_config:
                config.update(file_config['ai_narrative'])

    # Environment variable overrides
    env_key = os.environ.get('ANTHROPIC_API_KEY')
    if env_key:
        config['api_key'] = env_key

    # Enable if API key is configured
    if config['api_key']:
        config['enabled'] = True

    return config


def format_trend_data(trends, metric_name, num_periods=6):
    """Format trend data for the prompt."""
    if not trends:
        return "No data available"

    metric_aliases = {
        'median_sale_price': ('median_sale_price', 'median_price'),
        'median_price': ('median_price', 'median_sale_price'),
        'median_dom': ('median_dom', 'avg_dom'),
        'avg_dom': ('avg_dom', 'median_dom'),
        'inventory': ('inventory', 'total_inventory'),
        'total_inventory': ('total_inventory', 'inventory')
    }

    recent = trends[:num_periods]
    formatted = []

    for t in recent:
        period = t.get('period', 'Unknown')
        value = None
        for key in metric_aliases.get(metric_name, (metric_name,)):
            value = t.get(key)
            if value is not None:
                break

        if value is not None:
            if metric_name in ('median_price', 'median_sale_price'):
                formatted.append(f"{period}: ${value:,.0f}")
            elif metric_name in ('avg_dom', 'median_dom'):
                formatted.append(f"{period}: {value:,.0f} days")
            elif metric_name.endswith(('_mom', '_yoy')):
                formatted.append(f"{period}: {value*100:+.1f}%")
            else:
                formatted.append(f"{period}: {value:,.0f}")

    return ' -> '.join(formatted) if formatted else "No data available"


def build_narrative_prompt(summary, metro_trends):
    """Build the prompt for Claude to generate market narrative."""

    metro = summary.get('metro_name', 'Unknown Metro')
    period = summary.get('report_period', 'Unknown')
    health = summary.get('metro_health_score', 0)
    status = summary.get('market_status', 'UNKNOWN')
    description = summary.get('market_description', '')

    metrics = summary.get('key_metrics', {})
    city_tiers = summary.get('city_tiers', {})
    alerts = summary.get('alert_cities', [])
    top_cities = summary.get('top_cities', [])[:5]

    # Format trend strings
    price_trend = format_trend_data(metro_trends, 'median_sale_price')
    dom_trend = format_trend_data(metro_trends, 'median_dom')
    inventory_trend = format_trend_data(metro_trends, 'inventory')

    # Format city data
    city_summaries = []
    for city in top_cities:
        city_summaries.append(
            f"  - {city.get('name', 'Unknown')}: ${city.get('price', 0):,.0f} median, "
            f"{city.get('dom', 0)} DOM, {city.get('health', 0)} health score, "
            f"{city.get('price_yoy', 0)*100:+.1f}% YoY"
        )

    # Format alerts
    alert_summaries = []
    for alert in alerts[:3]:
        alert_summaries.append(
            f"  - {alert.get('name', 'Unknown')} ({alert.get('severity', 'LOW')}): "
            f"{', '.join(alert.get('alerts', []))}"
        )

    # Hot markets
    hot_markets = city_tiers.get('hot_markets', [])[:5]
    buyer_markets = city_tiers.get('buyer_markets', [])[:5]

    prompt = f"""You are a senior real estate market analyst providing a monthly market briefing for {metro}.
Based on the data below, write a compelling 3-4 paragraph market narrative suitable for real estate investors and agents.

MARKET DATA FOR {metro.upper()} - {period}:

Current Status:
- Market Health Score: {health}/100
- Classification: {status} - {description}
- Total Sales: {metrics.get('total_sales', 0):,}
- Active Inventory: {metrics.get('total_inventory', 0):,}
- Average Median Price: ${metrics.get('weighted_avg_price', 0):,.0f}
- Average Days on Market: {metrics.get('weighted_avg_dom', 0)} days

6-Month Trends:
- Price Trend: {price_trend}
- DOM Trend: {dom_trend}
- Inventory Trend: {inventory_trend}

Top Cities by Volume:
{chr(10).join(city_summaries) if city_summaries else '  No data available'}

Hot Markets (Strong Seller Conditions):
{', '.join(hot_markets) if hot_markets else 'None identified'}

Buyer Markets (Excess Inventory):
{', '.join(buyer_markets) if buyer_markets else 'None identified'}

Cities Requiring Attention:
{chr(10).join(alert_summaries) if alert_summaries else '  None flagged'}

INSTRUCTIONS:
1. Start with an executive summary of current market conditions (1 paragraph)
2. Analyze key trends and what they mean for the next 3-6 months (1 paragraph)
3. Provide specific guidance for different stakeholders:
   - For Sellers: pricing strategy and timeline expectations
   - For Buyers: negotiation approach and opportunity areas
   - For Investors: strategy recommendations (flip vs hold, target areas)
4. End with 2-3 specific actionable insights

Keep the tone professional but accessible. Use specific numbers from the data to support your analysis.
Do not use bullet points for the main narrative paragraphs - write in flowing prose.
The actionable insights at the end can be numbered or bulleted.
Total length should be approximately 400-500 words.
"""

    return prompt


def generate_narrative(summary, metro_trends, config=None, preview_only=False):
    """
    Generate AI-powered market narrative.

    Args:
        summary: Summary JSON dict
        metro_trends: List of trend data points
        config: Configuration dict (optional)
        preview_only: If True, return prompt without making API call

    Returns:
        dict with 'success', 'narrative', 'model', 'tokens_used'
    """
    if config is None:
        config = load_config()

    result = {
        'success': False,
        'narrative': '',
        'model': config.get('model', 'unknown'),
        'tokens_used': 0,
        'error': None
    }

    prompt = build_narrative_prompt(summary, metro_trends)

    if preview_only:
        result['success'] = True
        result['narrative'] = f"[PREVIEW - Prompt would be sent to {config['model']}]\n\n{prompt}"
        return result

    if not ANTHROPIC_AVAILABLE:
        result['error'] = "anthropic package not installed. Run: pip install anthropic"
        return result

    if not config.get('api_key'):
        result['error'] = "No API key configured. Set ANTHROPIC_API_KEY or configure in notifications_config.json"
        return result

    try:
        client = anthropic.Anthropic(api_key=config['api_key'])

        message = client.messages.create(
            model=config['model'],
            max_tokens=config.get('max_tokens', 2000),
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract narrative from response
        narrative = message.content[0].text if message.content else ''

        result['success'] = True
        result['narrative'] = narrative
        result['tokens_used'] = message.usage.input_tokens + message.usage.output_tokens

    except anthropic.APIConnectionError:
        result['error'] = "Failed to connect to Anthropic API"
    except anthropic.RateLimitError:
        result['error'] = "API rate limit exceeded. Please try again later."
    except anthropic.APIStatusError as e:
        result['error'] = f"API error: {e.message}"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"

    return result


def save_narrative(narrative, output_path):
    """Save narrative to file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(narrative)
    return output_path


def process_metro(metro_name, metro_dir, config, preview_only=False):
    """Process a single metro and generate narrative."""
    print(f"\n[PROCESS] {metro_name}")

    # Find latest period
    period_pattern = re.compile(r'^\d{4}-\d{2}$')
    period_folders = sorted([
        d for d in metro_dir.iterdir()
        if d.is_dir() and period_pattern.match(d.name)
    ], reverse=True)

    if not period_folders:
        print(f"  [SKIP] No data folders found")
        return None

    latest_folder = period_folders[0]
    summary_file = latest_folder / f"{metro_name}_summary.json"
    data_file = latest_folder / f"{metro_name}_data.json"

    if not summary_file.exists():
        print(f"  [SKIP] Summary file not found: {summary_file}")
        return None

    # Load summary
    with open(summary_file, 'r') as f:
        summary = json.load(f)

    # Load trends from data file
    metro_trends = []
    if data_file.exists():
        with open(data_file, 'r') as f:
            data = json.load(f)
            metro_trends = data.get('metro_trends', [])

    # Generate narrative
    result = generate_narrative(summary, metro_trends, config, preview_only)

    if result['success']:
        if preview_only:
            print(f"  [PREVIEW] Prompt generated ({len(result['narrative'])} chars)")
        else:
            # Save narrative
            output_path = latest_folder / f"{metro_name}_narrative.txt"
            save_narrative(result['narrative'], output_path)
            print(f"  [OK] Narrative saved: {output_path}")
            print(f"       Tokens used: {result['tokens_used']}")

            # Also save as JSON with metadata
            narrative_json = {
                'metro': summary.get('metro_name'),
                'period': summary.get('report_period'),
                'generated_at': datetime.now().isoformat(),
                'model': result['model'],
                'tokens_used': result['tokens_used'],
                'narrative': result['narrative']
            }
            json_path = latest_folder / f"{metro_name}_narrative.json"
            with open(json_path, 'w') as f:
                json.dump(narrative_json, f, indent=2)
    else:
        print(f"  [ERROR] {result['error']}")

    return result


def main():
    """Command-line entry point."""
    base_dir = Path(__file__).parent
    config = load_config()

    print("\n" + "="*60)
    print("AI MARKET NARRATIVE GENERATOR")
    print("="*60)

    # Check for preview mode
    preview_only = '--preview' in sys.argv

    if preview_only:
        print("[MODE] Preview only - no API calls will be made")

    # Check for specific metro
    metro_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == '--metro' and i + 1 < len(sys.argv):
            metro_filter = sys.argv[i + 1].lower()

    # Verify setup
    if not preview_only:
        if not ANTHROPIC_AVAILABLE:
            print("\n[ERROR] anthropic package not installed")
            print("        Run: pip install anthropic")
            return 1

        if not config.get('api_key'):
            print("\n[ERROR] No API key configured")
            print("        Set ANTHROPIC_API_KEY environment variable")
            print("        Or add to notifications_config.json")
            return 1

        print(f"\n[CONFIG] Model: {config['model']}")
        print(f"         Max tokens: {config['max_tokens']}")

    # Load metro config
    metro_config_file = base_dir / 'metro_config.json'
    if not metro_config_file.exists():
        print("[ERROR] metro_config.json not found")
        return 1

    with open(metro_config_file, 'r') as f:
        metro_config = json.load(f)

    metros = [m for m in metro_config.get('metros', []) if m.get('enabled', True)]

    if metro_filter:
        metros = [m for m in metros if m['name'].lower() == metro_filter]
        if not metros:
            print(f"[ERROR] Metro '{metro_filter}' not found or not enabled")
            return 1

    # Process each metro
    results = []
    total_tokens = 0

    for metro in metros:
        metro_name = metro['name']
        metro_dir = base_dir / metro.get('output_directory', metro_name)

        if not metro_dir.exists():
            print(f"\n[SKIP] {metro_name} - directory not found")
            continue

        result = process_metro(metro_name, metro_dir, config, preview_only)
        if result:
            results.append((metro_name, result))
            total_tokens += result.get('tokens_used', 0)

    # Summary
    print("\n" + "="*60)
    print("NARRATIVE GENERATION SUMMARY")
    print("="*60)

    successful = 0
    for metro_name, result in results:
        status = "[OK]" if result['success'] else "[FAILED]"
        if result['success']:
            successful += 1
        print(f"  {status} {metro_name}")
        if result.get('error'):
            print(f"         Error: {result['error']}")

    if not preview_only and total_tokens > 0:
        print(f"\nTotal API tokens used: {total_tokens:,}")
        # Rough cost estimate (Claude Sonnet pricing as of late 2024)
        estimated_cost = (total_tokens / 1000) * 0.003
        print(f"Estimated cost: ${estimated_cost:.4f}")

    return 0 if successful == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
