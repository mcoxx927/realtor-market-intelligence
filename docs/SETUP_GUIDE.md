# Complete Setup Guide - Real Estate Market Analysis Pipeline

## Table of Contents
1. [Windows Task Scheduler Setup](#windows-task-scheduler-setup)
2. [Google Workspace Email Configuration](#google-workspace-email-configuration)
3. [Security Best Practices](#security-best-practices)
4. [Testing Your Setup](#testing-your-setup)
5. [Troubleshooting](#troubleshooting)

---

## Windows Task Scheduler Setup

### Option 1: Automated Setup (Recommended)

Run the PowerShell setup script:

```powershell
# Navigate to project directory
cd "C:\Users\1\Documents\GitHub\realtor monthly data analysis"

# Run setup script (may require Administrator if prompted)
powershell -ExecutionPolicy Bypass -File setup_task_scheduler.ps1
```

This creates a scheduled task that:
- Runs every 4 weeks on Saturday at 9:00 AM
- **Runs even if the computer was off** (catches up when you turn it back on)
- Downloads fresh data automatically
- Processes all metros
- Sends email reports
- **Skips AI narrative generation** (no API costs)

### Option 2: Manual Setup

1. Open Task Scheduler (`Win + R`, type `taskschd.msc`)
2. Click "Create Task" (not "Create Basic Task")
3. **General Tab:**
   - Name: `RedfinMarketAnalysis`
   - Description: `Monthly Redfin market analysis pipeline`
   - Select: "Run whether user is logged on or not"
   - Check: "Run with highest privileges" (only if needed)

4. **Triggers Tab:**
   - Click "New"
   - Begin the task: "On a schedule"
   - Settings: "Weekly"
   - Recur every: `4` weeks
   - On: `Saturday`
   - Start: `9:00:00 AM`
   - Check: "Enabled"

5. **Actions Tab:**
   - Click "New"
   - Action: "Start a program"
   - Program/script: `python` (or full path: `C:\Python312\python.exe`)
   - Add arguments: `run_scheduled.py --no-ai`
   - Start in: `C:\Users\1\Documents\GitHub\realtor monthly data analysis`

6. **Conditions Tab:**
   - Uncheck: "Start the task only if the computer is on AC power"
   - Check: "Start the task only if the following network connection is available: Any connection"

7. **Settings Tab:**
   - Check: "Allow task to be run on demand"
   - Check: "Run task as soon as possible after a scheduled start is missed" ← **KEY FOR CATCHING UP**
   - Check: "If the task fails, restart every: 30 minutes, Attempt to restart up to: 2 times"
   - "If the running task does not end when requested": "Stop the existing instance"
   - Execution time limit: `4 hours`

8. Click OK and enter your Windows password if prompted

---

## Google Workspace Email Configuration

### Step 1: Generate App Password (REQUIRED for Google Workspace)

Google Workspace requires **App Passwords** instead of your regular password for SMTP access.

#### Generate App Password:

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security**
3. Enable **2-Step Verification** (required for App Passwords)
   - If not enabled, click "2-Step Verification" and follow setup
4. After 2FA is enabled, go back to Security
5. Click **App passwords** (search for "app passwords" if you don't see it)
6. Select:
   - App: **Mail**
   - Device: **Windows Computer** (or "Other" and type "Market Analysis Pipeline")
7. Click **Generate**
8. **Copy the 16-character password** (format: `xxxx xxxx xxxx xxxx`)
   - This is shown only once - save it immediately!

### Step 2: Configure Email Settings

#### Option A: Using notifications_config.json (Easier to manage)

Edit `notifications_config.json`:

```json
{
  "email": {
    "enabled": true,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your-email@yourdomain.com",
    "smtp_password": "xxxx xxxx xxxx xxxx",
    "from_address": "your-email@yourdomain.com",
    "recipients": [
      "recipient1@example.com",
      "recipient2@example.com"
    ],
    "send_on_success": true,
    "send_on_failure": true,
    "include_summary_attachment": true
  },
  "ai_narrative": {
    "enabled": false,
    "api_key": "",
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 2000
  }
}
```

**Important:**
- Use your **Google Workspace email** for `smtp_user` and `from_address`
- Use the **16-character App Password** for `smtp_password` (include spaces or remove them - both work)
- Add recipient emails to the `recipients` array

#### Option B: Using Environment Variables (More secure - see Security section)

Set these environment variables instead:

```powershell
# Set environment variables (only current session)
$env:SMTP_USER = "your-email@yourdomain.com"
$env:SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"
$env:EMAIL_FROM = "your-email@yourdomain.com"
$env:EMAIL_RECIPIENTS = "recipient1@example.com,recipient2@example.com"

# Or set permanently for your user account
[System.Environment]::SetEnvironmentVariable("SMTP_USER", "your-email@yourdomain.com", "User")
[System.Environment]::SetEnvironmentVariable("SMTP_PASSWORD", "xxxx xxxx xxxx xxxx", "User")
[System.Environment]::SetEnvironmentVariable("EMAIL_FROM", "your-email@yourdomain.com", "User")
[System.Environment]::SetEnvironmentVariable("EMAIL_RECIPIENTS", "recipient1@example.com,recipient2@example.com", "User")
```

### Step 3: Test Email Configuration

```bash
# Test email setup
python email_reports.py --test
```

You should receive a test email. If not, see Troubleshooting section.

---

## Security Best Practices

### Is it Safe to Store Passwords in JSON or .env?

**Short Answer:** On a local machine that only you access, it's reasonably safe but not perfect.

**Security Levels (Best to Worst):**

#### 1. Windows Credential Manager (MOST SECURE - Recommended)

Your credentials are encrypted by Windows using your user account.

**Coming Soon:** I can create a script that uses Windows Credential Manager instead of plain text.

#### 2. Environment Variables (GOOD - Recommended for now)

Credentials are stored in your user profile and not visible in the file system.

**Pros:**
- Not stored in files that could be accidentally committed to Git
- Requires access to your Windows user account
- Separate from code files

**Cons:**
- Visible to any process running as your user
- Lost if user profile is deleted

**How to use:**
1. Set environment variables (see Option B above)
2. Leave `smtp_password` empty in `notifications_config.json`
3. The script will automatically use environment variables

#### 3. JSON File (OKAY for local-only use)

**Pros:**
- Easy to configure
- All settings in one place

**Cons:**
- Password visible in plain text file
- Could be accidentally committed to Git (if you push this repo)

**If using JSON file:**

1. **Add to .gitignore** (I'll do this for you)
2. Make sure the file permissions restrict access to your user only
3. Never commit this file to a public repository

#### 4. .env File (Similar to JSON)

Similar security level to JSON. Commonly used but still plain text.

### Recommendations for Your Setup:

**For this local machine:**

Since you mentioned it's a local machine, here's what I recommend:

1. **Use Environment Variables** (Option 2) - This is the best balance of security and convenience
2. **Keep notifications_config.json for non-sensitive settings** (enabled flags, recipients, etc.)
3. **Add sensitive file to .gitignore** to prevent accidental commits

Let me update the `.gitignore` file right now:

---

## Testing Your Setup

### 1. Test Individual Components

```bash
# Test data fetcher
python fetch_redfin_data.py

# Test email (sends test email)
python email_reports.py --test

# Test complete pipeline without AI or email
python run_scheduled.py --no-ai --no-notify --dry-run
```

### 2. Test Full Pipeline (Dry Run)

```bash
# Simulates everything without actually executing
python run_scheduled.py --no-ai --dry-run
```

### 3. Test Full Pipeline (Real Run)

```bash
# Runs everything except AI narratives
python run_scheduled.py --no-ai
```

This will:
1. Check if data needs updating (downloads if stale)
2. Process all metros
3. Generate dashboards
4. Send email reports

### 4. Test Task Scheduler Task

```powershell
# Run the scheduled task immediately (for testing)
Start-ScheduledTask -TaskName "RedfinMarketAnalysis"

# Check task status
Get-ScheduledTaskInfo -TaskName "RedfinMarketAnalysis"

# View last run result (0 = success, non-zero = error)
(Get-ScheduledTaskInfo -TaskName "RedfinMarketAnalysis").LastTaskResult
```

---

## Troubleshooting

### Email Issues

#### "Authentication failed" or "Username and password not accepted"

**Cause:** Using regular password instead of App Password

**Solution:**
1. Generate a new App Password (see Google Workspace section)
2. Use the 16-character App Password, not your regular password
3. Make sure 2-Factor Authentication is enabled on your Google account

#### "SMTPServerDisconnected" or "Connection refused"

**Cause:** Wrong SMTP server or port

**Solution:**
- Google Workspace SMTP: `smtp.gmail.com:587`
- Ensure `smtp_port` is `587` (not 465 or 25)

#### Emails not sending but no errors

**Cause:** Email disabled in config

**Solution:**
Check `notifications_config.json`:
- `"enabled": true` must be set
- Recipients array must not be empty

### Task Scheduler Issues

#### Task shows "Running" but nothing happens

**Cause:** Python not in PATH or wrong working directory

**Solution:**
1. Use full path to python.exe in Task Action
2. Verify "Start in" directory is set correctly
3. Check `pipeline_runs.log` for errors

#### Task didn't run when computer was off

**Cause:** "Run task as soon as possible after scheduled start is missed" not checked

**Solution:**
1. Open Task Scheduler
2. Edit task → Settings tab
3. Check "Run task as soon as possible after a scheduled start is missed"

#### Task runs but fails immediately

**Cause:** Permission or dependency issues

**Solution:**
1. Check `pipeline_runs.log` for error details
2. Try running manually: `python run_scheduled.py --no-ai`
3. Ensure all dependencies are installed: `pip install pandas anthropic`

### Data Fetching Issues

#### "Download failed" or timeout errors

**Cause:** Network issues or Redfin server problems

**Solution:**
- The script automatically uses backup file if download fails
- Check your internet connection
- Try manual download: `python fetch_redfin_data.py --force`

### Pipeline Issues

#### "No data found for metro"

**Cause:** Missing or corrupted data files

**Solution:**
1. Check if `city_market_tracker.tsv000.gz` exists in project root
2. Re-download: `python fetch_redfin_data.py --force`
3. Run extraction manually: `python extract_metros.py`

---

## Advanced Configuration

### Running on Different Schedule

Edit the task trigger in Task Scheduler or modify `setup_task_scheduler.ps1`:

**Weekly on Fridays:**
```powershell
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "06:00PM"
```

**First day of every month:**
```powershell
$Trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At "08:00AM"
```

### Enabling AI Narratives

**WARNING:** This will incur API costs (approximately $0.01-0.03 per metro per run)

1. Get Anthropic API key from https://console.anthropic.com/
2. Add to environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")
   ```
3. Remove `--no-ai` flag from scheduled task
4. Test: `python ai_narrative.py --preview --metro charlotte`

### Multiple Email Recipients

In `notifications_config.json`:

```json
"recipients": [
  "investor1@example.com",
  "investor2@example.com",
  "analyst@example.com"
]
```

---

## Quick Reference Commands

```bash
# Manual pipeline run (original)
python run_market_analysis.py

# Automated pipeline without AI (recommended for scheduled tasks)
python run_scheduled.py --no-ai

# Test email configuration
python email_reports.py --test

# Download fresh data
python fetch_redfin_data.py --force

# Test scheduled task
Start-ScheduledTask -TaskName "RedfinMarketAnalysis"

# View task history
Get-ScheduledTaskInfo -TaskName "RedfinMarketAnalysis"

# Check pipeline log
notepad pipeline_runs.log
```

---

## Support

If you encounter issues:

1. Check `pipeline_runs.log` for detailed error messages
2. Run components individually to isolate the problem
3. Verify configurations in `notifications_config.json`
4. Check Task Scheduler task history (Action → View → Show Task History)

---

**Last Updated:** 2025-12-15
