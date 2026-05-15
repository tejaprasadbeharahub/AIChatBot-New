"""Connect to Google Sheets via the Google Sheets API and return a Pandas DataFrame."""

import json
import re
from typing import Optional

import pandas as pd
from fastapi import HTTPException

from app.core.config import settings


def _extract_sheet_id(url: str) -> str:
    """Parse the Sheets spreadsheet ID out of any Google Sheets URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Could not extract spreadsheet ID from the Google Sheets URL.",
        )
    return match.group(1)


def _get_credentials():
    """Build a google.oauth2 service-account Credentials object from config."""
    try:
        from google.oauth2 import service_account  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="google-auth package is not installed. Run: pip install google-auth",
        ) from exc

    sa_path = (settings.google_service_account_json or "").strip()
    if not sa_path:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not configured.",
        )

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    try:
        credentials = service_account.Credentials.from_service_account_file(
            sa_path, scopes=scopes
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load Google service-account credentials: {exc}",
        ) from exc
    return credentials


def load_google_sheet(
    sheet_url: str,
    sheet_tab: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch the given Google Sheet and return it as a DataFrame.
    Uses the Sheets v4 REST API via google-api-python-client.
    Raises HTTPException on configuration or API errors.
    """
    try:
        from googleapiclient.discovery import build  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="google-api-python-client is not installed. Run: pip install google-api-python-client",
        ) from exc

    sheet_id = _extract_sheet_id(sheet_url)
    credentials = _get_credentials()

    try:
        service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to access Google Sheet. Ensure the sheet is shared with the service account. Error: {exc}",
        ) from exc

    # Resolve tab name
    available_tabs: list[str] = [
        s["properties"]["title"] for s in spreadsheet.get("sheets", [])
    ]
    if not available_tabs:
        raise HTTPException(status_code=400, detail="The Google Sheet has no tabs.")

    target_tab = sheet_tab if sheet_tab else available_tabs[0]
    if target_tab not in available_tabs:
        raise HTTPException(
            status_code=400,
            detail=f"Tab '{target_tab}' not found. Available: {available_tabs}",
        )

    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=target_tab)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read data from Google Sheet tab '{target_tab}': {exc}",
        ) from exc

    rows = result.get("values", [])
    if not rows:
        raise HTTPException(status_code=400, detail="The selected sheet tab contains no data.")

    headers = [str(h).strip() for h in rows[0]]
    data_rows = rows[1:]

    # Pad or truncate each row to match header length
    padded: list[list] = []
    for row in data_rows:
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))
        padded.append(row[: len(headers)])

    df = pd.DataFrame(padded, columns=headers)
    if df.empty:
        raise HTTPException(status_code=400, detail="The Google Sheet tab contains no data rows.")
    return df


def get_google_sheet_tabs(sheet_url: str) -> list[str]:
    """Return tab names for a Google Sheet without loading any data."""
    try:
        from googleapiclient.discovery import build  # type: ignore
    except ImportError:
        return []

    sheet_id = _extract_sheet_id(sheet_url)
    credentials = _get_credentials()
    try:
        service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        return [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]
    except Exception:
        return []


def build_google_sheet_metadata(sheet_url: str, sheet_tab: Optional[str] = None) -> dict:
    """Return metadata dict parallel to file_loader.build_datasource_metadata."""
    available_tabs = get_google_sheet_tabs(sheet_url)
    df = load_google_sheet(sheet_url, sheet_tab=sheet_tab)

    sheet_id = _extract_sheet_id(sheet_url)
    resolved_tab = sheet_tab or (available_tabs[0] if available_tabs else None)

    return {
        "sheet_id": sheet_id,
        "resolved_tab": resolved_tab,
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names_json": json.dumps(list(df.columns)),
        "sheet_tabs_json": json.dumps(available_tabs) if available_tabs else None,
    }
