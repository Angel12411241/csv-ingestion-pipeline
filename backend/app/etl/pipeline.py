"""Pure Pandas ETL: bytes -> validated, cleaned DataFrame + a report. No database access here."""

import io
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from app.etl.constants import (
    CATEGORY_COLUMNS,
    COLUMN_MAP,
    CRITICAL_NUMERIC,
    CRITICAL_TEXT,
    DEDUPE_KEY,
    INTEGER_COLUMNS,
    MEDIAN_FILL_NUMERIC,
    NA_VALUES,
    ORDERDATE_FORMAT,
    REQUIRED_COLUMNS,
    UNKNOWN,
)


class ETLError(Exception):
    """Base class for errors caused by the uploaded file (reported to the client as 400)."""


class CSVParseError(ETLError):
    pass


class MissingColumnsError(ETLError):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"Missing required columns: {', '.join(missing)}")


@dataclass
class TransformReport:
    rows_in: int
    rows_out: int = 0
    dropped_missing_required: int = 0
    dropped_invalid_date: int = 0
    dropped_duplicates: int = 0
    date_min: date | None = None
    date_max: date | None = None
    total_sales: float = 0.0
    filled_with_median: dict[str, int] = field(default_factory=dict)

    @property
    def rows_dropped(self) -> int:
        return self.dropped_missing_required + self.dropped_invalid_date + self.dropped_duplicates

    @property
    def drop_breakdown(self) -> dict[str, int]:
        return {
            "missing_required": self.dropped_missing_required,
            "invalid_date": self.dropped_invalid_date,
            "duplicates": self.dropped_duplicates,
        }


def _decode(content: bytes) -> str:
    # The Kaggle file is latin-1 encoded (accented customer names), so it is not valid UTF-8.
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def extract(content: bytes) -> pd.DataFrame:
    """Parse raw CSV bytes into a DataFrame of strings with normalised (stripped, upper-case) headers."""
    if not content.strip():
        raise CSVParseError("The uploaded file is empty.")
    try:
        df = pd.read_csv(
            io.StringIO(_decode(content)),
            dtype=str,
            keep_default_na=False,
            na_values=NA_VALUES,
            skipinitialspace=True,
        )
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise CSVParseError(f"Could not parse CSV: {exc}") from exc

    df.columns = [str(c).strip().upper() for c in df.columns]
    if df.empty:
        raise CSVParseError("The CSV has a header but no data rows.")
    return df


def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise MissingColumnsError(missing)


def _parse_order_dates(raw: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(raw, format=ORDERDATE_FORMAT, errors="coerce")
    fallback = parsed.isna() & raw.notna()
    if fallback.any():
        parsed.loc[fallback] = pd.to_datetime(raw[fallback], format="mixed", errors="coerce")
    return parsed


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, TransformReport]:
    """Clean the extracted frame. Returns columns named after the `records` table plus a report."""
    validate_columns(df)
    df = df.copy()
    report = TransformReport(rows_in=len(df))

    # Normalise text: strip whitespace, treat blank strings as nulls.
    for col in df.columns:
        df[col] = df[col].str.strip().replace("", pd.NA)

    # Coerce numerics; anything non-numeric becomes NaN and is handled by the null policy below.
    numeric_cols = [c for c in (*CRITICAL_NUMERIC, *MEDIAN_FILL_NUMERIC, "ORDERLINENUMBER") if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Identifiers and counts must be whole numbers.
    for col in (c for c in INTEGER_COLUMNS if c in df.columns):
        df.loc[df[col] % 1 != 0, col] = np.nan

    # 1. Drop rows missing a critical field.
    critical_mask = df[[*CRITICAL_NUMERIC, *CRITICAL_TEXT]].isna().any(axis=1)
    report.dropped_missing_required = int(critical_mask.sum())
    df = df[~critical_mask].copy()

    # 2. Parse ORDERDATE; drop rows where it is missing or unparseable.
    df["ORDERDATE"] = _parse_order_dates(df["ORDERDATE"])
    date_mask = df["ORDERDATE"].isna()
    report.dropped_invalid_date = int(date_mask.sum())
    df = df[~date_mask].copy()

    # 3. Deduplicate on the business key, keeping the first occurrence.
    before = len(df)
    df = df.drop_duplicates(subset=DEDUPE_KEY, keep="first").copy()
    report.dropped_duplicates = before - len(df)

    # 4. Impute non-critical numeric nulls with the median of the cleaned data.
    for col in MEDIAN_FILL_NUMERIC:
        if col not in df.columns:
            continue
        nulls = int(df[col].isna().sum())
        median = df[col].median()
        if nulls and pd.notna(median):
            df[col] = df[col].fillna(median)
            report.filled_with_median[col] = nulls

    for col in CATEGORY_COLUMNS:
        df[col] = df[col].fillna(UNKNOWN)

    # 5. Derived column.
    df["TOTAL_SALES"] = (df["QUANTITYORDERED"] * df["PRICEEACH"]).round(2)

    for col in (c for c in INTEGER_COLUMNS if c in df.columns):
        df[col] = df[col].astype("Int64")

    report.rows_out = len(df)
    if report.rows_out:
        report.date_min = df["ORDERDATE"].min().date()
        report.date_max = df["ORDERDATE"].max().date()
        report.total_sales = round(float(df["SALES"].sum()), 2)

    df["ORDERDATE"] = df["ORDERDATE"].dt.date
    out = df[[c for c in COLUMN_MAP if c in df.columns]].rename(columns=COLUMN_MAP)
    # Optional columns absent from the file are stored as NULL.
    for target in COLUMN_MAP.values():
        if target not in out.columns:
            out[target] = None
    return out.reset_index(drop=True), report


def to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a transformed frame into plain-Python dicts ready for a bulk INSERT."""
    rows = df.to_dict(orient="records")
    return [{k: (None if v is None or (not isinstance(v, str) and pd.isna(v)) else v) for k, v in row.items()} for row in rows]
