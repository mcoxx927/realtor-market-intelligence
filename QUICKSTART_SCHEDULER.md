# Quick Start: Windows Task Scheduler Setup

This guide will get you up and running with automated monthly market analysis in under 10 minutes.

---

## Step 1: Setup Task Scheduler (2 minutes)

Open PowerShell in the project directory and run:

```powershell
powershell -ExecutionPolicy Bypass -File setup_task_scheduler.ps1
```

**What this does:**
- Creates a scheduled task that runs every 4 weeks on Saturday at 9 AM
- **Automatically catches up if your computer was off** when scheduled
- Runs the pipeline WITHOUT AI (no API costs)
- Takes about 15-30 minutes to complete when it runs

---

## Step 2: Configure Google Workspace Email (5 minutes)

### A. Generate App Password

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** (if not already enabled)
3. Click **App passwords**
4. Select "Mail" and "Windows Computer"
5. Click **Generate**
6. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### B. Configure Email Settings

**Option 1: Using Config File (Easier)**

1. Copy the template:
   ```powershell
   Copy-Item notifications_config.template.json notifications_config.json
   ```

2. Edit `notifications_config.json`:
   ```json
   {
     "email": {
       "enabled": true,
       "smtp_host": "smtp.gmail.com",
       "smtp_port": 587,
       "smtp_user": "your-email@yourdomain.com",
       "smtp_password": "abcd efgh ijkl mnop",
       "from_address": "your-email@yourdomain.com",
       "recipients": ["recipient@example.com"],
       "send_on_success": true,
       "send_on_failure": true
     }
   }
   ```

**Option 2: Using Environment Variables (More Secure)**

```powershell
[System.Environment]::SetEnvironmentVariable("SMTP_USER", "your-email@yourdomain.com", "User")
[System.Environment]::SetEnvironmentVariable("SMTP_PASSWORD", "abcd efgh ijkl mnop", "User")
[System.Environment]::SetEnvironmentVariable("EMAIL_FROM", "your-email@yourdomain.com", "User")
[System.Environment]::SetEnvironmentVariable("EMAIL_RECIPIENTS", "recipient@example.com", "User")
```

Then in `notifications_config.json`, just set `"enabled": true` and leave passwords blank.

---

## Step 3: Test Everything (3 minutes)

### Test Email:
```bash
python email_reports.py --test
```

You should receive a test email within 10 seconds.

### Test Full Pipeline (Dry Run):
```bash
python run_scheduled.py --no-ai --dry-run
```

This simulates the full pipeline without actually running it.

### Test Scheduled Task:
```powershell
Start-ScheduledTask -TaskName "RedfinMarketAnalysis"
```

Check `pipeline_runs.log` after a few minutes to see progress.

---

## How It Works

When the scheduled task runs:

1. **Downloads latest Redfin data** (if older than 35 days)
2. **Extracts metro data** for Charlotte and Roanoke
3. **Processes market metrics** with 12-month trends
4. **Generates interactive HTML dashboards**
5. **Creates strategic summaries** with recommendations
6. **Sends email reports** to configured recipients

**Total runtime:** 15-30 minutes depending on data size

---

## What If My Computer Is Off?

No problem! The task is configured with:
- **"Run task as soon as possible after scheduled start is missed"**

This means:
- If your computer is off at 9 AM Saturday, the task will run as soon as you turn it on
- You won't miss any scheduled runs

---

## Files Generated Each Run

```
charlotte/2025-XX/
├── charlotte_data.json              (13 MB - full data)
├── charlotte_summary.json           (18 KB - strategic analysis)
└── dashboard_enhanced_charlotte_2025-XX.html (9.5 MB - interactive)

roanoke/2025-XX/
├── roanoke_data.json                (3 MB - full data)
├── roanoke_summary.json             (18 KB - strategic analysis)
└── dashboard_enhanced_roanoke_2025-XX.html (2.7 MB - interactive)
```

---

## Security: Is My Password Safe?

### Config File Method
- **Reasonably safe** on a local machine you control
- Password is in plain text but only accessible to your Windows user account
- **Already added to .gitignore** so it won't be committed to Git

### Environment Variables Method (Recommended)
- **More secure** - stored in Windows registry encrypted by your user account
- Not visible in any files
- Survives even if you delete the config file

### Most Secure (Future Enhancement)
- Windows Credential Manager integration
- Let me know if you want this implemented

---

## Monitoring Your Scheduled Task

### View Task Status:
```powershell
Get-ScheduledTaskInfo -TaskName "RedfinMarketAnalysis"
```

### Check Last Run Result:
```powershell
# Returns 0 if successful, non-zero if failed
(Get-ScheduledTaskInfo -TaskName "RedfinMarketAnalysis").LastTaskResult
```

### View Execution Log:
```powershell
notepad pipeline_runs.log
```

### View in Task Scheduler GUI:
1. Press `Win + R`
2. Type `taskschd.msc`
3. Find "RedfinMarketAnalysis" in Task Scheduler Library
4. Right-click → Properties to view/edit settings

---

## Common Issues

### Email not sending?
- Verify you're using the **App Password**, not your regular password
- Check that 2-Factor Authentication is enabled on your Google account
- Run: `python email_reports.py --test`

### Task not running when computer was off?
- Open Task Scheduler
- Right-click task → Properties → Settings tab
- Verify "Run task as soon as possible after a scheduled start is missed" is checked

### Pipeline errors?
- Check `pipeline_runs.log` for detailed error messages
- Try running manually: `python run_scheduled.py --no-ai`

---

## Need More Details?

See **SETUP_GUIDE.md** for comprehensive documentation including:
- Troubleshooting steps
- Advanced configuration
- Enabling AI narratives (optional)
- Changing the schedule
- Multiple recipients

---

## Quick Commands Reference

```bash
# Test email
python email_reports.py --test

# Run pipeline manually (without AI)
python run_scheduled.py --no-ai

# Run task immediately
Start-ScheduledTask -TaskName "RedfinMarketAnalysis"

# Check task status
Get-ScheduledTaskInfo -TaskName "RedfinMarketAnalysis"

# View logs
notepad pipeline_runs.log

# Open dashboards
start charlotte\2025-10\dashboard_enhanced_charlotte_2025-10.html
```

---

**You're all set!** The pipeline will run automatically every month and send you email reports.
