# Discord Notifier

A simple Python-based Discord notification system designed to run via cron jobs.

## Quick Start

### 1. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Webhooks

**Error Webhook** (optional but recommended):
Copy the example file and add your webhook:
```bash
cp error_webhook.yaml.example error_webhook.yaml
```
Then edit `error_webhook.yaml` with your webhook URL.

**Notification Messages**:
Create YAML files in `configs/` (or any directory) for each notification:
```yaml
webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
message: |
  Hello! This is a notification.
  
  It supports multiple lines.
  Today's date is {date}.
```

### 3. Run Manually

```bash
./venv/bin/python3 discord_notifier.py configs/my_notification.yaml
```

### 4. Set Up Cron Job

```bash
crontab -e
```

Example cron entry:
```cron
# Send notification every day at 9:00 AM
0 9 * * * /home/Projects/generic-discord-notifier/venv/bin/python3 /home/Projects/generic-discord-notifier/discord_notifier.py /home/Projects/generic-discord-notifier/configs/morning.yaml
```

**Important:** Use absolute paths in cron jobs.

## Date Placeholders

Use date placeholders in your messages that are automatically replaced when the notification is sent:

- `{date}` - Current date in DD/MM/YYYY format (e.g., `25/12/2024`)
- `{date:DD/MM}` - Current date in DD/MM format (e.g., `25/12`)
- `{date:DD/MM/YYYY}` - Current date in DD/MM/YYYY format (e.g., `25/12/2024`)

Example:
```yaml
message: |
  Daily Report for {date:DD/MM}
  Today is {date:DD/MM/YYYY}
  Generated on {date}.
```

## Error Webhook

The error webhook (`error_webhook.yaml`) receives notifications when:
- A configuration file is missing or invalid
- Sending a notification fails (network issues, invalid webhook, etc.)

If the error webhook itself fails, errors are logged to stderr (visible in cron logs).

Error notifications include:
- Which configuration file failed
- Timestamp of the error
- Error type and message

## Getting Discord Webhook URLs

1. Go to your Discord server
2. Navigate to Server Settings → Integrations → Webhooks
3. Click "New Webhook" or select an existing webhook
4. Copy the webhook URL
5. Paste it into your configuration files

## Repository Setup

This repository is configured to keep your webhook URLs private:

- **`.gitignore`** excludes:
  - `error_webhook.yaml` (your real error webhook)
  - Personal config files in `configs/` (e.g., `check-in-*.yaml`)

- **Template files** (safe to commit):
  - `error_webhook.yaml.example` - Template for error webhook
  - `configs/example_notification.yaml.example` - Example notification config

**To set up locally:**
1. Copy `error_webhook.yaml.example` to `error_webhook.yaml` and add your webhook URL
2. Create your notification configs in `configs/` (they won't be committed)

**To initialize a new repository:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/generic-discord-notifier.git
git push -u origin main
```

Your webhook URLs will remain local and won't be pushed to GitHub.
