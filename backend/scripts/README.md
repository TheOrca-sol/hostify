# Hostify Background Workers

This directory contains background worker scripts that handle automatic tasks for the Hostify application.

## Workers

### 1. Calendar Sync Worker (`sync_calendars.py`)

Automatically syncs property calendars based on their configured sync frequency.

**Features:**
- Checks all active properties with calendar URLs
- Syncs based on each property's `sync_frequency` setting (1, 3, 6, 12, or 24 hours)
- Updates `last_sync` timestamp after successful syncs
- Runs continuously, checking every 5 minutes

**Usage:**
```bash
# Run continuously (recommended for production)
cd backend
python scripts/sync_calendars.py

# Run once and exit (useful for testing)
python scripts/sync_calendars.py once
```

### 2. Message Sending Worker (`send_scheduled_messages.py`)

Automatically sends scheduled messages (SMS, email) based on their scheduled time.

**Features:**
- Finds and sends all due scheduled messages
- Handles SMS and email delivery
- Updates message status after sending
- Runs continuously, checking every 60 seconds

**Usage:**
```bash
cd backend
python scripts/send_scheduled_messages.py
```

### 3. Combined Worker Starter (`start_workers.py`)

Starts both workers simultaneously in separate processes.

**Usage:**
```bash
cd backend
python scripts/start_workers.py
```

## Production Deployment

For production deployment, you should use a process manager like:

### Using systemd (Linux)

Create service files:

**`/etc/systemd/system/hostify-calendar-sync.service`:**
```ini
[Unit]
Description=Hostify Calendar Sync Worker
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/hostify/backend
Environment=PATH=/path/to/hostify/backend/venv/bin
ExecStart=/path/to/hostify/backend/venv/bin/python scripts/sync_calendars.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/hostify-message-worker.service`:**
```ini
[Unit]
Description=Hostify Message Sending Worker
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/hostify/backend
Environment=PATH=/path/to/hostify/backend/venv/bin
ExecStart=/path/to/hostify/backend/venv/bin/python scripts/send_scheduled_messages.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start the services:
```bash
sudo systemctl enable hostify-calendar-sync
sudo systemctl enable hostify-message-worker
sudo systemctl start hostify-calendar-sync
sudo systemctl start hostify-message-worker
```

### Using Docker

Add to your `docker-compose.yml`:
```yaml
services:
  calendar-sync:
    build: ./backend
    command: python scripts/sync_calendars.py
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
    restart: unless-stopped

  message-worker:
    build: ./backend
    command: python scripts/send_scheduled_messages.py
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
    restart: unless-stopped
```

## Monitoring

### Check Worker Status

**Calendar Sync Worker:**
```bash
# Check if running
ps aux | grep sync_calendars.py

# Check logs (if using systemd)
sudo journalctl -u hostify-calendar-sync -f
```

**Message Worker:**
```bash
# Check if running
ps aux | grep send_scheduled_messages.py

# Check logs (if using systemd)
sudo journalctl -u hostify-message-worker -f
```

### Manual Sync

To manually trigger a calendar sync for testing:
```bash
cd backend
python scripts/sync_calendars.py once
```

## Configuration

### Environment Variables

Make sure these environment variables are set:
- `DATABASE_URL`: PostgreSQL connection string
- `FIREBASE_CREDENTIALS`: Firebase service account credentials
- `TWILIO_ACCOUNT_SID`: Twilio account SID (for SMS)
- `TWILIO_AUTH_TOKEN`: Twilio auth token (for SMS)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`: Email configuration

### Sync Frequency

Property sync frequency is configured when creating/editing properties:
- 1 hour: Every hour
- 3 hours: Every 3 hours (default)
- 6 hours: Every 6 hours
- 12 hours: Every 12 hours
- 24 hours: Once a day

## Troubleshooting

### Common Issues

1. **Workers not starting:**
   - Check Python environment and dependencies
   - Verify database connection
   - Check environment variables

2. **Sync not happening:**
   - Verify property has valid `ical_url`
   - Check `sync_frequency` setting
   - Look for errors in worker logs

3. **Messages not sending:**
   - Verify SMS/email credentials
   - Check message templates
   - Look for errors in worker logs

### Logs

Workers output detailed logs to stdout. Monitor these for:
- Sync success/failure messages
- Error details
- Performance metrics
- Next sync timing information
