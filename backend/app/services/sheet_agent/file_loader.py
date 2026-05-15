"""Load CSV / XLSX files from disk into Pandas DataFrames."""

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import HTTPException


_MAX_ROWS = 50_000  # safety cap to avoid OOM on large files


def load_dataframe(storage_path: str, sheet_tab: Optional[str] = None) -> pd.DataFrame:
    """
    Load a CSV or XLSX file at *storage_path* into a DataFrame.
    For XLSX files, ``sheet_tab`` selects a specific tab; if omitted, the first sheet is used.
    Raises HTTPException on invalid/unreadable files.
    """
    path = Path(storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Data file not found: {path.name}")

    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            df = _load_csv(path)
        elif suffix in {".xlsx", ".xls"}:
            df = _load_xlsx(path, sheet_tab=sheet_tab)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {exc}") from exc

    if df.empty:
        raise HTTPException(status_code=400, detail="The file contains no data rows.")

    if len(df) > _MAX_ROWS:
        df = df.head(_MAX_ROWS)

    # Normalise column names to strings to avoid any integer column issues
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _load_csv(path: Path) -> pd.DataFrame:
    # Try UTF-8 first, fall back to latin-1
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")


def _load_xlsx(path: Path, sheet_tab: Optional[str]) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    available_sheets = xl.sheet_names

    if not available_sheets:
        raise HTTPException(status_code=400, detail="The XLSX file contains no sheets.")

    if sheet_tab:
        if sheet_tab not in available_sheets:
            raise HTTPException(
                status_code=400,
                detail=f"Sheet tab '{sheet_tab}' not found. Available: {available_sheets}",
            )
        return xl.parse(sheet_tab)

    return xl.parse(available_sheets[0])


def get_xlsx_sheet_tabs(storage_path: str) -> list[str]:
    """Return the list of sheet tab names in an XLSX file."""
    path = Path(storage_path)
    if not path.exists():
        return []
    try:
        xl = pd.ExcelFile(path)
        return xl.sheet_names
    except Exception:
        return []


def build_datasource_metadata(
    storage_path: str, sheet_tab: Optional[str] = None
) -> dict:
    """
    Return metadata dict with keys: row_count, column_count, column_names_json, sheet_tabs_json.
    """
    path = Path(storage_path)
    suffix = path.suffix.lower()

    df = load_dataframe(storage_path, sheet_tab=sheet_tab)
    column_names_json = json.dumps(list(df.columns))

    sheet_tabs_json: Optional[str] = None
    if suffix in {".xlsx", ".xls"}:
        tabs = get_xlsx_sheet_tabs(storage_path)
        sheet_tabs_json = json.dumps(tabs)

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names_json": column_names_json,
        "sheet_tabs_json": sheet_tabs_json,
    }
