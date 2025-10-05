# gcal-sync

Sync the google calendar from the past and future

## Description

This script uses a Google Cloud service account to read calendar events from yesterday and tomorrow.

## Setup

### 1. VENV

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Calendar Access

The service account needs access to your Google Calendar. To grant access:

1. Open your [Google Calendar](https://calendar.google.com)
2. Go to Settings → Settings for my calendars → Select your calendar
3. Scroll to "Share with specific people or groups"
4. Click "Add people" and add the service account email (found in `calendar-sync-474218-57b5b0734c0e.json` as `client_email`)
5. Give it at least "See all event details" permission

### 4. Run the Script

```bash
python sync_calendar.py
```

## Features

- Reads events from yesterday (previous day)
- Reads events from tomorrow (next day)
- Displays event details including:
  - Title
  - Time
  - Location (if available)
  - Description preview (if available)
- Supports both all-day events and timed events

## Service Account

The script uses service account authentication with the credentials file:

- `calendar-sync-474218-57b5b0734c0e.json`

Make sure this file is present in the project root directory.
