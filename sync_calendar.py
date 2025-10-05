#!/usr/bin/env python3
"""
Google Calendar Sync Script
Reads calendar events from yesterday and tomorrow using a service account.
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Service account credentials file
SERVICE_ACCOUNT_FILE = 'calendar-sync-474218-57b5b0734c0e.json'

# Define the required scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_calendar_service():
    """
    Create and return a Google Calendar API service object using service account credentials.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except FileNotFoundError:
        print(f"Error: Service account file '{SERVICE_ACCOUNT_FILE}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error creating calendar service: {e}")
        exit(1)


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


def format_event(event):
    """
    Format an event for display.

    Args:
        event: Event dictionary from Google Calendar API

    Returns:
        Formatted string representation of the event
    """
    summary = event.get('summary', 'No Title')
    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))

    # Format datetime strings for better readability
    try:
        if 'T' in start:  # DateTime format
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
        else:  # Date-only format (all-day event)
            time_str = "All day"
    except Exception:
        time_str = f"{start} - {end}"

    description = event.get('description', '')
    location = event.get('location', '')

    output = f"  • {summary}\n"
    output += f"    Time: {time_str}\n"
    if location:
        output += f"    Location: {location}\n"
    if description:
        # Limit description to first 100 characters
        desc_preview = description[:100] + "..." if len(description) > 100 else description
        output += f"    Description: {desc_preview}\n"

    return output


def main():
    """
    Main function to fetch and display calendar events.
    """
    print("=" * 60)
    print("Google Calendar Sync")
    print("=" * 60)

    # Get today's date
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    print(f"\nToday: {today.strftime('%A, %B %d, %Y')}")
    print(f"Fetching events for:")
    print(f"  - Yesterday: {yesterday.strftime('%A, %B %d, %Y')}")
    print(f"  - Tomorrow: {tomorrow.strftime('%A, %B %d, %Y')}")
    print()

    # Create Calendar service
    service = get_calendar_service()

    # Default calendar ID for the service account's primary calendar
    # Note: Service accounts have their own calendar, but to access a user's calendar,
    # the user needs to share their calendar with the service account email
    calendar_id = 'primary'

    print("Note: To access a user's calendar, share the calendar with the service")
    print("      account email found in your credentials file.")
    print()

    # Fetch events for yesterday
    print("-" * 60)
    print(f"YESTERDAY - {yesterday.strftime('%A, %B %d, %Y')}")
    print("-" * 60)
    yesterday_events = get_events_for_date(service, calendar_id, yesterday)

    if yesterday_events:
        print(f"Found {len(yesterday_events)} event(s):\n")
        for event in yesterday_events:
            print(format_event(event))
    else:
        print("No events found.\n")

    # Fetch events for tomorrow
    print("-" * 60)
    print(f"TOMORROW - {tomorrow.strftime('%A, %B %d, %Y')}")
    print("-" * 60)
    tomorrow_events = get_events_for_date(service, calendar_id, tomorrow)

    if tomorrow_events:
        print(f"Found {len(tomorrow_events)} event(s):\n")
        for event in tomorrow_events:
            print(format_event(event))
    else:
        print("No events found.\n")

    print("=" * 60)
    print(f"Total events: {len(yesterday_events) + len(tomorrow_events)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
