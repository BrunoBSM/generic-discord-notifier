# Discord Notifier

Scheduled Discord notifications via webhooks, managed through a local web UI. Made for your home server/lab.

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run_web.py --host 0.0.0.0
```

Open `http://localhost:5000` → Create a notification → Enable it with a schedule.

## Web UI

The web dashboard lets you:
- Create and edit notifications (webhook URL + message)
- Enable/disable scheduling with preset times or custom cron expressions
- Send test notifications
- Manage the error webhook

Run on LAN: `python run_web.py --host 0.0.0.0 --port 5000`

The UI only needs to run when making changes—cron handles the actual notifications.

## CLI Usage

For automation or scripting, the following command will send a notification:

```bash
./venv/bin/python3 discord_notifier.py configs/my_notification.yaml
```

## Date Placeholders

Use in messages—replaced at send time:

| Placeholder | Output |
|-------------|--------|
| `{date}` | 25/12/2024 |
| `{date:DD/MM}` | 25/12 |
| `{date:DD/MM/YYYY}` | 25/12/2024 |

## Config Format

YAML files in `configs/`:

```yaml
webhook_url: "https://discord.com/api/webhooks/..."
message: |
  Hello! Today is {date}.
```

## Error Webhook

Optional. Receives alerts when notifications fail. Configure in Settings or `error_webhook.yaml`.

## Getting Webhook URLs

Discord Server → Settings → Integrations → Webhooks → New Webhook → Copy URL

## Privacy

You run on your machine or personal server. Your webhook URLs stay local.
