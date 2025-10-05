#!/usr/bin/env python3
"""
Google Calendar Sync Script
Reads calendar events from yesterday and tomorrow using a service account.
Dumps events as JSON to Google Drive.
"""

import json
import os
from datetime import datetime, timedelta
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload


# Service account credentials file
SERVICE_ACCOUNT_FILE = 'calendar-sync-474218-57b5b0734c0e.json'

# Define the required scopes for Google Calendar and Drive API
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.file'
]

# Google Drive Shared Drive ID and folder
# Your Shared Drive: "Service drive" / "Calendar Sync" folder
DRIVE_FOLDER_ID = '10IsYzQmX60XB0PgyIy7_ZF3kwcoH8iTZ'  # Calendar Sync folder
USE_SHARED_DRIVE = True  # Required for Shared Drives


def get_credentials():
    """
    Get service account credentials.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        return credentials
    except FileNotFoundError:
        print(f"Error: Service account file '{SERVICE_ACCOUNT_FILE}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        exit(1)


def get_calendar_service():
    """
    Create and return a Google Calendar API service object.
    """
    try:
        credentials = get_credentials()
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error creating calendar service: {e}")
        exit(1)


def get_drive_service():
    """
    Create and return a Google Drive API service object.
    """
    try:
        credentials = get_credentials()
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error creating drive service: {e}")
        exit(1)


def upload_json_to_drive(drive_service, data, filename):
    """
    Upload JSON data to Google Drive (supports Shared Drives).

    Args:
        drive_service: Google Drive API service object
        data: Dictionary to be saved as JSON
        filename: Name of the file to create in Drive

    Returns:
        File ID if successful, None otherwise
    """
    try:
        # Convert data to JSON string
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        # Create file metadata
        file_metadata = {
            'name': filename,
            'parents': [DRIVE_FOLDER_ID],
            'mimeType': 'application/json'
        }

        # Create media upload
        media = MediaIoBaseUpload(
            BytesIO(json_str.encode('utf-8')),
            mimetype='application/json',
            resumable=True
        )

        # Upload file (with Shared Drive support)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink',
            supportsAllDrives=USE_SHARED_DRIVE  # Required for Shared Drives
        ).execute()

        print(f"✅ Uploaded: {file.get('name')}")
        print(f"   File ID: {file.get('id')}")
        print(f"   Link: {file.get('webViewLink')}")

        return file.get('id')
    except HttpError as error:
        print(f"❌ Error uploading to Drive: {error}")
        return None


def get_events_for_date(service, calendar_id, target_date):
    """
    Get all events for a specific date.

    Args:
        service: Google Calendar API service object
        calendar_id: ID of the calendar to query
        target_date: datetime object for the target date

    Returns:
        List of events for the specified date
    """
    # Set time range for the entire day (00:00:00 to 23:59:59)
    time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    time_max = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Convert to RFC3339 format for the API
    time_min_str = time_min.isoformat() + 'Z'
    time_max_str = time_max.isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min_str,
            timeMax=time_max_str,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return events
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []



def main():
    """
    Main function to fetch calendar events and upload to Drive.
    """
    print("=" * 40)
    print("Google Calendar Sync → Drive")
    print("=" * 40)

    # Get today's date
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    print(f"\nToday: {today.strftime('%A, %B %d, %Y')}")
    print(f"Fetching events for:")
    print(f"  - Yesterday: {yesterday.strftime('%A, %B %d, %Y')}")
    print(f"  - Tomorrow: {tomorrow.strftime('%A, %B %d, %Y')}")
    print()

    # Create Calendar and Drive services
    calendar_service = get_calendar_service()
    drive_service = get_drive_service()

    # Calendar ID
    calendar_id = 'c_ac7393b8d3f127d084622613884cb7b2467816515da9e5a6f7a22ccf5845be42@group.calendar.google.com'

    # Fetch events for yesterday
    print("-" * 40)
    print(f"📅 YESTERDAY - {yesterday.strftime('%A, %B %d, %Y')}")
    yesterday_events = get_events_for_date(calendar_service, calendar_id, yesterday)

    if yesterday_events:
        print(f"Found {len(yesterday_events)} event(s)")
    else:
        print("No events found")

    # Fetch events for tomorrow
    print()
    print("-" * 40)
    print(f"📅 TOMORROW - {tomorrow.strftime('%A, %B %d, %Y')}")
    tomorrow_events = get_events_for_date(calendar_service, calendar_id, tomorrow)

    if tomorrow_events:
        print(f"Found {len(tomorrow_events)} event(s)")
    else:
        print("No events found")

    # Prepare data for upload
    total_events = len(yesterday_events) + len(tomorrow_events)
    print()
    print("=" * 40)
    print(f"Total events: {total_events}")

    # Create separate JSON files for yesterday (reality) and tomorrow (expectation)
    reality_data = {
        "sync_timestamp": today.isoformat(),
        "date": yesterday.strftime('%Y-%m-%d'),
        "day_name": yesterday.strftime('%A'),
        "type": "reality",
        "event_count": len(yesterday_events),
        "events": yesterday_events
    }

    expectation_data = {
        "sync_timestamp": today.isoformat(),
        "date": tomorrow.strftime('%Y-%m-%d'),
        "day_name": tomorrow.strftime('%A'),
        "type": "expectation",
        "event_count": len(tomorrow_events),
        "events": tomorrow_events
    }

    # Generate filenames with DD-MM-YYYY format
    reality_filename = f"{yesterday.strftime('%d-%m-%Y')}-reality.json"
    expectation_filename = f"{tomorrow.strftime('%d-%m-%Y')}-expectation.json"

    # Save and upload files
    print()
    print("💾 Processing files...")
    print("-" * 40)

    uploaded_files = []

    # Process reality file (yesterday)
    print(f"\n1️⃣  Reality file: {reality_filename}")
    with open(reality_filename, 'w', encoding='utf-8') as f:
        json.dump(reality_data, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Saved locally")

    file_id = upload_json_to_drive(drive_service, reality_data, reality_filename)
    if file_id:
        uploaded_files.append(reality_filename)
        print(f"   ✅ Uploaded to Drive")

    # Process expectation file (tomorrow)
    print(f"\n2️⃣  Expectation file: {expectation_filename}")
    with open(expectation_filename, 'w', encoding='utf-8') as f:
        json.dump(expectation_data, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Saved locally")

    file_id = upload_json_to_drive(drive_service, expectation_data, expectation_filename)
    if file_id:
        uploaded_files.append(expectation_filename)
        print(f"   ✅ Uploaded to Drive")

    # Clean up local files after successful upload
    print()
    print("🧹 Cleaning up local files...")
    print("-" * 40)
    for filename in uploaded_files:
        try:
            os.remove(filename)
            print(f"   🗑️  Deleted: {filename}")
        except Exception as e:
            print(f"   ⚠️  Could not delete {filename}: {e}")

    print()
    print("=" * 40)
    print("✨ Sync completed!")
    print(f"📊 Uploaded {len(uploaded_files)} file(s) to Drive")
    print("=" * 40)


if __name__ == '__main__':
    main()
