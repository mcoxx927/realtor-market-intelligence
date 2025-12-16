"""
Email Reports Module
Sends automated market analysis reports via email.

Usage:
    python email_reports.py                    # Send reports for all metros
    python email_reports.py --metro charlotte  # Send report for specific metro
    python email_reports.py --test             # Send test email

Environment Variables (or use notifications_config.json):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_RECIPIENTS
"""

import os
import sys
import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


def load_config():
    """Load email configuration from file or environment variables."""
    base_dir = Path(__file__).parent
    config_file = base_dir / 'notifications_config.json'

    config = {
        'enabled': False,
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_user': '',
        'smtp_password': '',
        'from_address': '',
        'recipients': [],
        'send_on_success': True,
        'send_on_failure': True,
        'include_summary_attachment': True
    }

    # Load from config file if exists
    if config_file.exists():
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            if 'email' in file_config:
                config.update(file_config['email'])

    # Environment variables override config file
    env_mappings = {
        'SMTP_HOST': 'smtp_host',
        'SMTP_PORT': 'smtp_port',
        'SMTP_USER': 'smtp_user',
        'SMTP_PASSWORD': 'smtp_password',
        'EMAIL_FROM': 'from_address',
        'EMAIL_RECIPIENTS': 'recipients'
    }

    for env_var, config_key in env_mappings.items():
        env_value = os.environ.get(env_var)
        if env_value:
            if env_var == 'SMTP_PORT':
                config[config_key] = int(env_value)
            elif env_var == 'EMAIL_RECIPIENTS':
                config[config_key] = [r.strip() for r in env_value.split(',')]
            else:
                config[config_key] = env_value

    # Enable if credentials are configured
    if config['smtp_user'] and config['smtp_password'] and config['recipients']:
        config['enabled'] = True

    return config


def generate_email_html(summary, include_ai_narrative=None):
    """Generate HTML email body from summary JSON."""
    metro = summary.get('metro_name', 'Unknown Metro')
    period = summary.get('report_period', 'Unknown')
    health = summary.get('metro_health_score', 0)
    status = summary.get('market_status', 'UNKNOWN')
    description = summary.get('market_description', '')

    metrics = summary.get('key_metrics', {})
    recommendations = summary.get('recommendations', {})
    city_tiers = summary.get('city_tiers', {})
    alerts = summary.get('alert_cities', [])

    # Status colors
    status_colors = {
        'BULLISH': '#28a745',
        'SLIGHTLY_BULLISH': '#5cb85c',
        'NEUTRAL': '#ffc107',
        'SLIGHTLY_BEARISH': '#fd7e14',
        'BEARISH': '#dc3545'
    }
    status_color = status_colors.get(status, '#6c757d')

    # Health score color
    if health >= 60:
        health_color = '#28a745'
    elif health >= 40:
        health_color = '#ffc107'
    else:
        health_color = '#dc3545'

    # Format price
    avg_price = metrics.get('weighted_avg_price', 0)
    price_formatted = f"${avg_price:,.0f}" if avg_price else "N/A"

    # Build hot markets list
    hot_markets = city_tiers.get('hot_markets', [])
    hot_list = ', '.join(hot_markets[:5]) if hot_markets else 'None identified'

    # Build alerts section
    alerts_html = ''
    high_alerts = [a for a in alerts if a.get('severity') == 'HIGH']
    medium_alerts = [a for a in alerts if a.get('severity') == 'MEDIUM']

    if high_alerts or medium_alerts:
        alerts_html = '<h3 style="color: #dc3545; margin-top: 20px;">Cities Requiring Attention</h3>'
        alerts_html += '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">'
        alerts_html += '<tr style="background: #f8f9fa;"><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">City</th>'
        alerts_html += '<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Severity</th>'
        alerts_html += '<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Issues</th></tr>'

        for alert in (high_alerts + medium_alerts)[:5]:
            severity_color = '#dc3545' if alert['severity'] == 'HIGH' else '#fd7e14'
            issues = ', '.join(alert.get('alerts', []))
            alerts_html += f'''
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{alert.get('name', '')}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: {severity_color}; font-weight: bold;">{alert.get('severity', '')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{issues}</td>
            </tr>
            '''
        alerts_html += '</table>'

    # AI Narrative section
    ai_section = ''
    if include_ai_narrative:
        ai_section = f'''
        <div style="background: #e8f4f8; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #17a2b8;">
            <h3 style="color: #17a2b8; margin-top: 0;">AI Market Analysis</h3>
            <div style="line-height: 1.6;">{include_ai_narrative.replace(chr(10), '<br>')}</div>
        </div>
        '''

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{metro} Market Report - {period}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.5; color: #333; max-width: 700px; margin: 0 auto; padding: 20px;">

        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="margin: 0 0 10px 0; font-size: 24px;">{metro} Market Report</h1>
            <p style="margin: 0; opacity: 0.8;">Period: {period} | Generated: {datetime.now().strftime('%B %d, %Y')}</p>
        </div>

        <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 150px; background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: {health_color};">{health}</div>
                <div style="color: #6c757d; font-size: 14px;">Health Score</div>
            </div>
            <div style="flex: 1; min-width: 150px; background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="font-size: 18px; font-weight: bold; color: {status_color}; padding: 10px;">{status.replace('_', ' ')}</div>
                <div style="color: #6c757d; font-size: 14px;">Market Status</div>
            </div>
            <div style="flex: 1; min-width: 150px; background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #333;">{price_formatted}</div>
                <div style="color: #6c757d; font-size: 14px;">Avg. Median Price</div>
            </div>
        </div>

        <div style="background: #fff; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1a1a2e;">Market Overview</h3>
            <p>{description}</p>

            <table style="width: 100%; margin-top: 15px;">
                <tr>
                    <td style="padding: 5px 0;"><strong>Total Sales:</strong></td>
                    <td>{metrics.get('total_sales', 0):,}</td>
                    <td style="padding: 5px 0;"><strong>Active Inventory:</strong></td>
                    <td>{metrics.get('total_inventory', 0):,}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Avg. DOM:</strong></td>
                    <td>{metrics.get('weighted_avg_dom', 0)} days</td>
                    <td style="padding: 5px 0;"><strong>Cities Analyzed:</strong></td>
                    <td>{metrics.get('cities_analyzed', 0)}</td>
                </tr>
            </table>
        </div>

        <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745;">
            <h3 style="color: #155724; margin-top: 0;">Hot Markets</h3>
            <p style="margin-bottom: 0;">{hot_list}</p>
        </div>

        {alerts_html}

        <div style="background: #fff; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin-top: 20px;">
            <h3 style="margin-top: 0; color: #1a1a2e;">Recommendations</h3>

            <div style="margin-bottom: 15px;">
                <strong style="color: #28a745;">For Sellers:</strong>
                <p style="margin: 5px 0 0 0;">{recommendations.get('sellers', 'N/A')}</p>
            </div>

            <div style="margin-bottom: 15px;">
                <strong style="color: #17a2b8;">For Buyers:</strong>
                <p style="margin: 5px 0 0 0;">{recommendations.get('buyers', 'N/A')}</p>
            </div>

            <div>
                <strong style="color: #6f42c1;">For Investors:</strong>
                <p style="margin: 5px 0 0 0;">{recommendations.get('investors', 'N/A')}</p>
            </div>
        </div>

        {ai_section}

        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 12px;">
            <p>This report was automatically generated by the Real Estate Market Analysis Pipeline.</p>
            <p>Data Source: Redfin Data Center | Analysis Period: {period}</p>
        </div>

    </body>
    </html>
    '''

    return html


def generate_plain_text(summary):
    """Generate plain text version of email."""
    metro = summary.get('metro_name', 'Unknown Metro')
    period = summary.get('report_period', 'Unknown')
    health = summary.get('metro_health_score', 0)
    status = summary.get('market_status', 'UNKNOWN')
    metrics = summary.get('key_metrics', {})
    recommendations = summary.get('recommendations', {})

    text = f"""
{metro} Market Report - {period}
{'='*50}

MARKET STATUS: {status.replace('_', ' ')}
Health Score: {health}/100

KEY METRICS:
- Total Sales: {metrics.get('total_sales', 0):,}
- Active Inventory: {metrics.get('total_inventory', 0):,}
- Avg. Median Price: ${metrics.get('weighted_avg_price', 0):,.0f}
- Avg. Days on Market: {metrics.get('weighted_avg_dom', 0)} days
- Cities Analyzed: {metrics.get('cities_analyzed', 0)}

RECOMMENDATIONS:

For Sellers:
{recommendations.get('sellers', 'N/A')}

For Buyers:
{recommendations.get('buyers', 'N/A')}

For Investors:
{recommendations.get('investors', 'N/A')}

---
Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}
Data Source: Redfin Data Center
"""
    return text


def send_email(config, subject, html_body, text_body, attachments=None):
    """Send email with HTML body and optional attachments."""
    if not config.get('enabled'):
        print("[SKIP] Email not configured (missing credentials or recipients)")
        return False

    if not config.get('recipients'):
        print("[SKIP] No email recipients configured")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config['from_address'] or config['smtp_user']
        msg['To'] = ', '.join(config['recipients'])

        # Attach plain text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Add attachments if any
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(filepath)
                        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                        msg.attach(part)

        # Connect and send
        print(f"[EMAIL] Connecting to {config['smtp_host']}:{config['smtp_port']}...")

        with smtplib.SMTP(config['smtp_host'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['smtp_user'], config['smtp_password'])
            server.send_message(msg)

        print(f"[OK] Email sent to {len(config['recipients'])} recipient(s)")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[ERROR] Email authentication failed. Check username/password.")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to send email: {str(e)}")
        return False


def send_market_report(metro_name, summary, config=None, ai_narrative=None):
    """Send market report email for a specific metro."""
    if config is None:
        config = load_config()

    period = summary.get('report_period', 'Unknown')
    status = summary.get('market_status', 'UNKNOWN').replace('_', ' ')

    subject = f"[Market Report] {metro_name} - {period} ({status})"

    html_body = generate_email_html(summary, include_ai_narrative=ai_narrative)
    text_body = generate_plain_text(summary)

    # Prepare attachments
    attachments = []
    if config.get('include_summary_attachment'):
        base_dir = Path(__file__).parent
        summary_file = base_dir / metro_name.lower() / period / f"{metro_name.lower()}_summary.json"
        if summary_file.exists():
            attachments.append(str(summary_file))

    return send_email(config, subject, html_body, text_body, attachments)


def send_pipeline_notification(success, message, metros_processed=None, config=None):
    """Send notification about pipeline execution status."""
    if config is None:
        config = load_config()

    status_emoji = "Success" if success else "FAILED"
    subject = f"[Pipeline {status_emoji}] Real Estate Market Analysis - {datetime.now().strftime('%Y-%m-%d')}"

    metros_list = ', '.join(metros_processed) if metros_processed else 'None'

    html_body = f'''
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: {'#28a745' if success else '#dc3545'};">Pipeline Execution {'Completed' if success else 'Failed'}</h2>
        <p><strong>Time:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        <p><strong>Status:</strong> {message}</p>
        <p><strong>Metros Processed:</strong> {metros_list}</p>
        {'<p style="color: #28a745;">All dashboards and reports have been generated successfully.</p>' if success else '<p style="color: #dc3545;">Please check the logs for details.</p>'}
    </body>
    </html>
    '''

    text_body = f"""
Pipeline Execution {'Completed' if success else 'Failed'}
{'='*50}

Time: {datetime.now().strftime('%B %d, %Y at %H:%M')}
Status: {message}
Metros Processed: {metros_list}

{'All dashboards and reports have been generated successfully.' if success else 'Please check the logs for details.'}
"""

    # Decide whether to send based on config
    if success and not config.get('send_on_success', True):
        print("[SKIP] Success notification disabled in config")
        return True

    if not success and not config.get('send_on_failure', True):
        print("[SKIP] Failure notification disabled in config")
        return True

    return send_email(config, subject, html_body, text_body)


def send_test_email(config=None):
    """Send a test email to verify configuration."""
    if config is None:
        config = load_config()

    subject = "[TEST] Real Estate Market Analysis Email Configuration"

    html_body = f'''
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #17a2b8;">Email Configuration Test</h2>
        <p>This is a test email from the Real Estate Market Analysis Pipeline.</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
        <p style="color: #28a745;">If you received this email, your configuration is working correctly!</p>
    </body>
    </html>
    '''

    text_body = f"""
Email Configuration Test
{'='*50}

This is a test email from the Real Estate Market Analysis Pipeline.

Timestamp: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}

If you received this email, your configuration is working correctly!
"""

    return send_email(config, subject, html_body, text_body)


def main():
    """Command-line entry point."""
    import re

    base_dir = Path(__file__).parent
    config = load_config()

    print("\n" + "="*60)
    print("EMAIL REPORTS MODULE")
    print("="*60)

    # Check for test mode
    if '--test' in sys.argv:
        print("\n[TEST] Sending test email...")
        success = send_test_email(config)
        return 0 if success else 1

    # Check for specific metro
    metro_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == '--metro' and i + 1 < len(sys.argv):
            metro_filter = sys.argv[i + 1].lower()

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

    # Send reports for each metro
    results = []
    for metro in metros:
        metro_name = metro['name']
        metro_dir = base_dir / metro.get('output_directory', metro_name)

        # Find latest summary file
        period_pattern = re.compile(r'^\d{4}-\d{2}$')
        period_folders = sorted([
            d for d in metro_dir.iterdir()
            if d.is_dir() and period_pattern.match(d.name)
        ], reverse=True)

        if not period_folders:
            print(f"[SKIP] No data found for {metro_name}")
            continue

        latest_folder = period_folders[0]
        summary_file = latest_folder / f"{metro_name}_summary.json"

        if not summary_file.exists():
            print(f"[SKIP] Summary file not found: {summary_file}")
            continue

        with open(summary_file, 'r') as f:
            summary = json.load(f)

        # Check for AI narrative
        ai_narrative = None
        narrative_file = latest_folder / f"{metro_name}_narrative.txt"
        if narrative_file.exists():
            with open(narrative_file, 'r') as f:
                ai_narrative = f.read()

        print(f"\n[SEND] Sending report for {metro['display_name']}...")
        success = send_market_report(
            metro['display_name'],
            summary,
            config=config,
            ai_narrative=ai_narrative
        )
        results.append((metro_name, success))

    # Summary
    print("\n" + "="*60)
    print("EMAIL REPORT SUMMARY")
    print("="*60)
    for metro_name, success in results:
        status = "[OK]" if success else "[FAILED]"
        print(f"  {status} {metro_name}")

    return 0 if all(r[1] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
