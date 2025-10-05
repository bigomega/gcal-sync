#!/usr/bin/env python3
"""
Helper script to list all Shared Drives accessible by the service account.
Use this to find the correct Shared Drive ID.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'calendar-sync-474218-57b5b0734c0e.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def list_shared_drives():
    """List all Shared Drives accessible by the service account."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)

        print("=" * 70)
        print("Shared Drives Accessible by Service Account")
        print("=" * 70)
        print()

        # List all shared drives
        results = service.drives().list(
            pageSize=100,
            fields='drives(id, name, kind)'
        ).execute()

        drives = results.get('drives', [])

        if not drives:
            print("❌ No Shared Drives found!")
            print()
            print("To fix this:")
            print("1. Go to Google Drive → Shared drives")
            print("2. Create a new Shared Drive (or use existing)")
            print("3. Add the service account as a member:")
            print("   background-script@calendar-sync-474218.iam.gserviceaccount.com")
            print("4. Give it 'Content manager' or 'Manager' role")
            print()
            return

        print(f"Found {len(drives)} Shared Drive(s):\n")

        for i, drive in enumerate(drives, 1):
            drive_id = drive['id']
            name = drive.get('name', 'No Name')

            print(f"{i}. {name}")
            print(f"   ID: {drive_id}")
            print(f"   Type: {drive.get('kind', 'N/A')}")
            print()

            # Try to list files in this drive
            try:
                files_result = service.files().list(
                    driveId=drive_id,
                    corpora='drive',
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    pageSize=5,
                    fields='files(id, name)'
                ).execute()
                files = files_result.get('files', [])
                if files:
                    print(f"   Sample files ({len(files)}):")
                    for file in files[:3]:
                        print(f"     - {file.get('name')}")
                else:
                    print(f"   (Empty drive)")
                print()
            except Exception as e:
                print(f"   ⚠️  Could not list files: {e}")
                print()

        print("=" * 70)
        print("Copy one of the Shared Drive IDs above to use in your script")
        print("Update DRIVE_FOLDER_ID in sync_calendar.py")
        print("=" * 70)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    list_shared_drives()
