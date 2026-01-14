#!/usr/bin/env python3
"""
Setup Google Drive test folder for Registry Review project discovery.

Creates the folder structure:
  Registry Review Projects/
    Botany-Farm-C06-006/
      project_manifest.json
      *.pdf (all PDFs from examples/22-23/)

Uses gcloud CLI with service account impersonation for authentication.
"""

import json
import subprocess
import requests
from pathlib import Path

SERVICE_ACCOUNT = "rag-ingestion-bot@koi-sensor.iam.gserviceaccount.com"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
PARENT_FOLDER_NAME = "Registry Review Projects"
PROJECT_FOLDER_NAME = "Botany-Farm-C06-006"

EXAMPLES_DIR = Path(__file__).parent.parent / "examples" / "22-23"

PROJECT_MANIFEST = {
    "project_name": "Botany Farm - 2022/23 Monitoring Period",
    "methodology": "Regen Network Methodology for Soil Organic Carbon v1.2.2",
    "project_id": "C06-006",
    "proponent": {
        "name": "Botany Farm Pty Ltd",
        "email": "botany@example.com"
    },
    "submitted_at": "2024-01-15T10:30:00Z",
    "notes": "Annual monitoring report for the 2022-2023 period. Includes baseline and monitoring reports."
}


def get_access_token() -> str:
    """Get access token with full Drive permissions."""
    result = subprocess.run(
        [
            "gcloud", "auth", "print-access-token",
            f"--impersonate-service-account={SERVICE_ACCOUNT}",
            f"--scopes={DRIVE_SCOPE}",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gcloud auth failed: {result.stderr}")
    return result.stdout.strip()


def drive_request(method: str, endpoint: str, token: str, **kwargs) -> requests.Response:
    """Make a Google Drive API request."""
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    url = f"https://www.googleapis.com/drive/v3/{endpoint}"
    response = requests.request(method, url, headers=headers, timeout=60, **kwargs)
    return response


def upload_request(method: str, url: str, token: str, **kwargs) -> requests.Response:
    """Make an upload request to Google Drive."""
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, url, headers=headers, timeout=120, **kwargs)
    return response


def find_folder(name: str, parent_id: str | None, token: str) -> str | None:
    """Find a folder by name, optionally within a parent folder."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    resp = drive_request("GET", "files", token, params={"q": query, "fields": "files(id,name)"})
    resp.raise_for_status()
    files = resp.json().get("files", [])
    return files[0]["id"] if files else None


def create_folder(name: str, parent_id: str | None, token: str) -> str:
    """Create a folder, returning its ID."""
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    resp = drive_request(
        "POST", "files", token,
        headers={"Content-Type": "application/json"},
        json=metadata,
    )
    resp.raise_for_status()
    folder_id = resp.json()["id"]
    print(f"  Created folder: {name} ({folder_id})")
    return folder_id


def find_or_create_folder(name: str, parent_id: str | None, token: str) -> str:
    """Find existing folder or create a new one."""
    existing = find_folder(name, parent_id, token)
    if existing:
        print(f"  Found existing folder: {name} ({existing})")
        return existing
    return create_folder(name, parent_id, token)


def upload_file(filepath: Path, parent_id: str, token: str, mime_type: str = "application/pdf") -> str:
    """Upload a file to Google Drive using resumable upload for large files."""
    import io

    metadata = {
        "name": filepath.name,
        "parents": [parent_id],
    }

    # Step 1: Initiate resumable upload
    init_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
    init_resp = upload_request(
        "POST", init_url, token,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        json=metadata,
    )
    if init_resp.status_code not in (200, 308):
        print(f"   ✗ Failed to initiate upload: {init_resp.status_code} - {init_resp.text}")
        raise RuntimeError(f"Upload initiation failed: {init_resp.text}")

    upload_url = init_resp.headers.get("Location")
    if not upload_url:
        raise RuntimeError("No upload URL returned")

    # Step 2: Upload file content
    with open(filepath, "rb") as f:
        file_content = f.read()

    upload_resp = requests.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": mime_type,
            "Content-Length": str(len(file_content)),
        },
        data=file_content,
        timeout=300,
    )
    upload_resp.raise_for_status()
    file_id = upload_resp.json()["id"]
    print(f"  Uploaded: {filepath.name} ({file_id})")
    return file_id


def upload_json(content: dict, filename: str, parent_id: str, token: str) -> str:
    """Upload JSON content as a file using resumable upload."""
    metadata = {
        "name": filename,
        "parents": [parent_id],
    }

    # Step 1: Initiate resumable upload
    init_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
    init_resp = upload_request(
        "POST", init_url, token,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        json=metadata,
    )
    if init_resp.status_code not in (200, 308):
        print(f"   ✗ Failed to initiate upload: {init_resp.status_code} - {init_resp.text}")
        raise RuntimeError(f"Upload initiation failed: {init_resp.text}")

    upload_url = init_resp.headers.get("Location")
    if not upload_url:
        raise RuntimeError("No upload URL returned")

    # Step 2: Upload JSON content
    file_content = json.dumps(content, indent=2).encode("utf-8")

    upload_resp = requests.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Content-Length": str(len(file_content)),
        },
        data=file_content,
        timeout=60,
    )
    if upload_resp.status_code != 200:
        print(f"   ✗ Upload failed: {upload_resp.status_code}")
        print(f"   Response: {upload_resp.text}")
        upload_resp.raise_for_status()
    file_id = upload_resp.json()["id"]
    print(f"  Uploaded: {filename} ({file_id})")
    return file_id


def main():
    print("=" * 60)
    print("Setting up Google Drive test folder for Registry Review")
    print("=" * 60)

    # Get access token
    print("\n1. Authenticating with Google Drive...")
    token = get_access_token()
    print("   ✓ Authenticated")

    # Create/find parent folder
    print(f"\n2. Setting up parent folder: {PARENT_FOLDER_NAME}")
    parent_id = find_or_create_folder(PARENT_FOLDER_NAME, None, token)

    # Create/find project subfolder
    print(f"\n3. Setting up project folder: {PROJECT_FOLDER_NAME}")
    project_id = find_or_create_folder(PROJECT_FOLDER_NAME, parent_id, token)

    # Upload project manifest
    print("\n4. Uploading project_manifest.json...")
    upload_json(PROJECT_MANIFEST, "project_manifest.json", project_id, token)

    # Upload PDF files
    print("\n5. Uploading PDF files from examples/22-23/...")
    pdf_files = list(EXAMPLES_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"   ⚠ No PDF files found in {EXAMPLES_DIR}")
    else:
        for pdf in sorted(pdf_files):
            upload_file(pdf, project_id, token)

    # Print summary
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print(f"\nParent Folder ID: {parent_id}")
    print(f"Project Folder ID: {project_id}")
    print(f"\nTo use this folder, set the environment variable:")
    print(f"  GDRIVE_PROJECTS_FOLDER_ID={parent_id}")
    print("\nOr add to your .env file:")
    print(f"  GDRIVE_PROJECTS_FOLDER_ID={parent_id}")


if __name__ == "__main__":
    main()
