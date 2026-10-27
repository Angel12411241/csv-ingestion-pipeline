from datetime import date

import pytest

from app.etl.pipeline import MissingColumnsError, extract, transform
from tests.conftest import fixture_bytes


def run(name: str):
    return transform(extract(fixture_bytes(name)))


def test_clean_file_keeps_all_rows_and_adds_derived_column():
    df, report = run("sample_sales.csv")

    assert report.rows_in == report.rows_out == 6
    assert report.rows_dropped == 0
    assert (report.date_min, report.date_max) == (date(2003, 2, 24), date(2003, 10, 28))
    assert report.total_sales == pytest.approx(21952.97)
    assert df.iloc[0]["total_sales"] == pytest.approx(30 * 95.70)


def test_dirty_file_dedupes_drops_invalid_rows_and_fills_nulls():
    """dirty_sales.csv: 7 rows -> 1 duplicate, 2 missing/invalid numerics, 1 bad date, 3 kept."""
    df, report = run("dirty_sales.csv")

    assert report.drop_breakdown == {"missing_required": 2, "invalid_date": 1, "duplicates": 1}
    assert len(df) == 3
    # Duplicate ORDERNUMBER + PRODUCTCODE: the first occurrence wins.
    assert df.loc[df["order_number"] == 10100, "quantity_ordered"].tolist() == [30]
    # Missing MSRP is filled with the median of the remaining values (170, 80).
    assert df.loc[df["order_number"] == 10103, "msrp"].iloc[0] == 125
    # ISO dates are parsed too, not just the dataset's M/D/YYYY format.
    assert df.loc[df["order_number"] == 10103, "order_date"].iloc[0] == date(2003, 2, 15)


def test_missing_required_columns_are_rejected():
    with pytest.raises(MissingColumnsError) as exc_info:
        run("missing_columns.csv")
    assert exc_info.value.missing == ["SALES", "PRODUCTLINE"]


def test_latin1_file_is_decoded():
    df = extract("ORDERNUMBER,CUSTOMERNAME\n1,Café Señor\n".encode("latin-1"))
    assert df.loc[0, "CUSTOMERNAME"] == "Café Señor"
