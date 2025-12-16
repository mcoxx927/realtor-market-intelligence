"""
Scheduled Pipeline Execution
Wrapper script for automated/scheduled runs with notifications.

This script:
1. Fetches latest Redfin data (if needed)
2. Runs the complete analysis pipeline
3. Generates AI narratives (if configured)
4. Sends email notifications with reports

Usage:
    python run_scheduled.py              # Full run with notifications
    python run_scheduled.py --no-fetch   # Skip data fetch
    python run_scheduled.py --no-notify  # Skip notifications
    python run_scheduled.py --no-ai      # Skip AI narrative generation
    python run_scheduled.py --dry-run    # Simulate without executing

Windows Task Scheduler Setup:
    schtasks /create /tn "RedfinMarketAnalysis" /tr "python C:\\path\\to\\run_scheduled.py" /sc monthly /d SAT /mo THIRD

Linux/Mac Cron (third Saturday at 9 AM):
    0 9 15-21 * 6 [ $(date +\\%u) -eq 6 ] && python /path/to/run_scheduled.py
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import traceback


def log_message(message, log_file=None):
    """Log message to console and optionally to file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted = f"[{timestamp}] {message}"
    print(formatted)

    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(formatted + '\n')


def load_schedule_config():
    """Load schedule configuration."""
    base_dir = Path(__file__).parent
    config_file = base_dir / 'notifications_config.json'

    config = {
        'log_file': 'pipeline_runs.log',
        'max_log_entries': 100,
        'retry_on_failure': True,
        'max_retries': 2
    }

    if config_file.exists():
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            if 'schedule' in file_config:
                config.update(file_config['schedule'])

    return config


def run_script(script_name, log_file=None, dry_run=False):
    """Run a Python script and capture results."""
    log_message(f"Running: {script_name}", log_file)

    if dry_run:
        log_message(f"  [DRY-RUN] Would execute: python {script_name}", log_file)
        return True, "Dry run - skipped"

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.returncode == 0:
            log_message(f"  [OK] {script_name} completed", log_file)
            return True, result.stdout
        else:
            log_message(f"  [FAILED] {script_name} returned {result.returncode}", log_file)
            if result.stderr:
                log_message(f"  Error: {result.stderr[:500]}", log_file)
            return False, result.stderr

    except subprocess.TimeoutExpired:
        log_message(f"  [TIMEOUT] {script_name} exceeded time limit", log_file)
        return False, "Script timed out"
    except Exception as e:
        log_message(f"  [ERROR] {script_name}: {str(e)}", log_file)
        return False, str(e)


def run_module_function(module_name, function_name, *args, log_file=None, dry_run=False, **kwargs):
    """Import and run a function from a module."""
    log_message(f"Running: {module_name}.{function_name}()", log_file)

    if dry_run:
        log_message(f"  [DRY-RUN] Would execute: {module_name}.{function_name}()", log_file)
        return True, "Dry run - skipped"

    try:
        # Add base directory to path
        base_dir = Path(__file__).parent
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        module = __import__(module_name)
        func = getattr(module, function_name)
        result = func(*args, **kwargs)

        log_message(f"  [OK] {function_name} completed", log_file)
        return True, result

    except Exception as e:
        log_message(f"  [ERROR] {function_name}: {str(e)}", log_file)
        return False, str(e)


def get_processed_metros(base_dir):
    """Get list of metros that were processed."""
    metro_config_file = base_dir / 'metro_config.json'
    if not metro_config_file.exists():
        return []

    with open(metro_config_file, 'r') as f:
        metro_config = json.load(f)

    return [m['display_name'] for m in metro_config.get('metros', []) if m.get('enabled', True)]


def run_scheduled_pipeline(skip_fetch=False, skip_notify=False, skip_ai=False, dry_run=False):
    """
    Run the complete scheduled pipeline.

    Args:
        skip_fetch: Skip data fetching step
        skip_notify: Skip email notifications
        skip_ai: Skip AI narrative generation
        dry_run: Simulate without executing

    Returns:
        dict with execution results
    """
    base_dir = Path(__file__).parent
    config = load_schedule_config()
    log_file = str(base_dir / config['log_file'])

    results = {
        'success': False,
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'steps': {},
        'errors': [],
        'metros_processed': []
    }

    log_message("", log_file)
    log_message("=" * 60, log_file)
    log_message("SCHEDULED PIPELINE EXECUTION", log_file)
    log_message("=" * 60, log_file)

    if dry_run:
        log_message("[MODE] Dry run - no actual execution", log_file)

    try:
        # Step 1: Fetch Redfin Data
        if not skip_fetch:
            log_message("\n[STEP 1/5] Fetching Redfin data...", log_file)
            success, output = run_module_function(
                'fetch_redfin_data', 'fetch_redfin_data',
                log_file=log_file, dry_run=dry_run
            )
            results['steps']['fetch_data'] = {'success': success, 'output': str(output)[:500]}

            if not success and not dry_run:
                # Check if we can continue with existing data
                data_file = base_dir / 'city_market_tracker.tsv000.gz'
                if data_file.exists():
                    log_message("  [WARN] Fetch failed but existing data found, continuing...", log_file)
                else:
                    results['errors'].append("Data fetch failed and no existing data")
                    raise Exception("Cannot continue without data file")
        else:
            log_message("\n[STEP 1/5] Skipping data fetch (--no-fetch)", log_file)
            results['steps']['fetch_data'] = {'success': True, 'output': 'Skipped'}

        # Step 2: Extract Metros
        log_message("\n[STEP 2/5] Extracting metro data...", log_file)
        success, output = run_script(
            str(base_dir / 'extract_metros.py'),
            log_file=log_file, dry_run=dry_run
        )
        results['steps']['extract_metros'] = {'success': success, 'output': str(output)[:500]}
        if not success and not dry_run:
            results['errors'].append("Metro extraction failed")
            raise Exception("Metro extraction failed")

        # Step 3: Process Market Data
        log_message("\n[STEP 3/5] Processing market data...", log_file)
        success, output = run_script(
            str(base_dir / 'process_market_data.py'),
            log_file=log_file, dry_run=dry_run
        )
        results['steps']['process_data'] = {'success': success, 'output': str(output)[:500]}
        if not success and not dry_run:
            results['errors'].append("Data processing failed")
            raise Exception("Data processing failed")

        # Step 4: Generate Dashboards
        log_message("\n[STEP 4/5] Generating dashboards...", log_file)
        success, output = run_script(
            str(base_dir / 'generate_dashboards_v2.py'),
            log_file=log_file, dry_run=dry_run
        )
        results['steps']['generate_dashboards'] = {'success': success, 'output': str(output)[:500]}
        if not success and not dry_run:
            results['errors'].append("Dashboard generation failed")
            raise Exception("Dashboard generation failed")

        # Step 5: Extract Summaries
        log_message("\n[STEP 5/5] Extracting summaries...", log_file)
        success, output = run_script(
            str(base_dir / 'extract_summary.py'),
            log_file=log_file, dry_run=dry_run
        )
        results['steps']['extract_summary'] = {'success': success, 'output': str(output)[:500]}
        if not success and not dry_run:
            results['errors'].append("Summary extraction failed")
            raise Exception("Summary extraction failed")

        # Get list of processed metros
        results['metros_processed'] = get_processed_metros(base_dir)

        # Optional: AI Narrative Generation
        if not skip_ai:
            log_message("\n[OPTIONAL] Generating AI narratives...", log_file)

            # Check if AI is configured
            try:
                from ai_narrative import load_config as load_ai_config
                ai_config = load_ai_config()

                if ai_config.get('enabled') or ai_config.get('api_key'):
                    success, output = run_script(
                        str(base_dir / 'ai_narrative.py'),
                        log_file=log_file, dry_run=dry_run
                    )
                    results['steps']['ai_narrative'] = {'success': success, 'output': str(output)[:500]}
                else:
                    log_message("  [SKIP] AI narrative not configured (no API key)", log_file)
                    results['steps']['ai_narrative'] = {'success': True, 'output': 'Not configured'}
            except ImportError:
                log_message("  [SKIP] ai_narrative module not available", log_file)
                results['steps']['ai_narrative'] = {'success': True, 'output': 'Module not available'}
        else:
            log_message("\n[OPTIONAL] Skipping AI narratives (--no-ai)", log_file)
            results['steps']['ai_narrative'] = {'success': True, 'output': 'Skipped'}

        # Pipeline completed successfully
        results['success'] = True
        log_message("\n[OK] PIPELINE COMPLETED SUCCESSFULLY", log_file)

    except Exception as e:
        log_message(f"\n[FAILED] Pipeline error: {str(e)}", log_file)
        results['errors'].append(str(e))
        traceback.print_exc()

    finally:
        results['end_time'] = datetime.now().isoformat()

        # Send notifications
        if not skip_notify and not dry_run:
            log_message("\n[NOTIFY] Sending notifications...", log_file)
            try:
                from email_reports import send_pipeline_notification, send_market_report, load_config

                email_config = load_config()

                if email_config.get('enabled'):
                    # Send pipeline status notification
                    status_msg = "All steps completed successfully" if results['success'] else f"Failed: {', '.join(results['errors'])}"
                    send_pipeline_notification(
                        results['success'],
                        status_msg,
                        metros_processed=results['metros_processed'],
                        config=email_config
                    )

                    # Send individual market reports if pipeline succeeded
                    if results['success']:
                        log_message("  Sending market reports...", log_file)
                        import re
                        for metro_name in results['metros_processed']:
                            # Find summary for this metro
                            metro_slug = metro_name.split(',')[0].lower().replace(' ', '_')
                            if 'charlotte' in metro_slug:
                                metro_slug = 'charlotte'
                            elif 'roanoke' in metro_slug:
                                metro_slug = 'roanoke'

                            metro_dir = base_dir / metro_slug
                            if metro_dir.exists():
                                period_pattern = re.compile(r'^\d{4}-\d{2}$')
                                period_folders = sorted([
                                    d for d in metro_dir.iterdir()
                                    if d.is_dir() and period_pattern.match(d.name)
                                ], reverse=True)

                                if period_folders:
                                    summary_file = period_folders[0] / f"{metro_slug}_summary.json"
                                    narrative_file = period_folders[0] / f"{metro_slug}_narrative.txt"

                                    if summary_file.exists():
                                        with open(summary_file, 'r') as f:
                                            summary = json.load(f)

                                        # Load AI narrative if available
                                        ai_narrative = None
                                        if narrative_file.exists():
                                            with open(narrative_file, 'r', encoding='utf-8') as f:
                                                ai_narrative = f.read()

                                        send_market_report(metro_name, summary, email_config, ai_narrative)

                    log_message("  [OK] Notifications sent", log_file)
                else:
                    log_message("  [SKIP] Email not configured", log_file)

            except Exception as e:
                log_message(f"  [ERROR] Notification failed: {str(e)}", log_file)
        elif skip_notify:
            log_message("\n[NOTIFY] Skipping notifications (--no-notify)", log_file)

    # Final summary
    log_message("\n" + "=" * 60, log_file)
    log_message("EXECUTION SUMMARY", log_file)
    log_message("=" * 60, log_file)
    log_message(f"Status: {'SUCCESS' if results['success'] else 'FAILED'}", log_file)
    log_message(f"Duration: {results['start_time']} to {results['end_time']}", log_file)
    log_message(f"Metros: {', '.join(results['metros_processed']) if results['metros_processed'] else 'None'}", log_file)

    if results['errors']:
        log_message(f"Errors: {', '.join(results['errors'])}", log_file)

    for step_name, step_result in results['steps'].items():
        status = '[OK]' if step_result['success'] else '[FAILED]'
        log_message(f"  {status} {step_name}", log_file)

    log_message("=" * 60, log_file)

    return results


def main():
    """Command-line entry point."""
    skip_fetch = '--no-fetch' in sys.argv
    skip_notify = '--no-notify' in sys.argv
    skip_ai = '--no-ai' in sys.argv
    dry_run = '--dry-run' in sys.argv

    results = run_scheduled_pipeline(
        skip_fetch=skip_fetch,
        skip_notify=skip_notify,
        skip_ai=skip_ai,
        dry_run=dry_run
    )

    return 0 if results['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
