"""Column contract for the Kaggle "Sample Sales Data" CSV (sales_data_sample.csv)."""

# A file must contain all of these (after header normalisation) or it is rejected.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "ORDERNUMBER",
    "PRODUCTCODE",
    "QUANTITYORDERED",
    "PRICEEACH",
    "SALES",
    "ORDERDATE",
    "STATUS",
    "PRODUCTLINE",
    "COUNTRY",
)

# Rows missing any of these cannot be stored meaningfully, so they are dropped.
# They are the dedupe key (ORDERNUMBER + PRODUCTCODE) and the inputs of TOTAL_SALES / SALES stats.
CRITICAL_NUMERIC: tuple[str, ...] = ("ORDERNUMBER", "QUANTITYORDERED", "PRICEEACH", "SALES")
INTEGER_COLUMNS: tuple[str, ...] = ("ORDERNUMBER", "QUANTITYORDERED", "ORDERLINENUMBER")
CRITICAL_TEXT: tuple[str, ...] = ("PRODUCTCODE",)

# Non-critical numeric measures: nulls are imputed with the column median.
MEDIAN_FILL_NUMERIC: tuple[str, ...] = ("MSRP",)

# Categorical dimensions used for filtering/charts: nulls become "Unknown" rather than dropping the sale.
CATEGORY_COLUMNS: tuple[str, ...] = ("STATUS", "PRODUCTLINE", "COUNTRY")
UNKNOWN = "Unknown"

DEDUPE_KEY: list[str] = ["ORDERNUMBER", "PRODUCTCODE"]

# The dataset's native format, e.g. "2/24/2003 0:00". Other formats fall back to inference.
ORDERDATE_FORMAT = "%m/%d/%Y %H:%M"

# Pandas treats "NA" as null by default, but in this dataset TERRITORY="NA" means North America.
NA_VALUES: list[str] = ["", "NULL", "null", "NaN", "nan", "N/A", "n/a", "None"]

# CSV column -> records table column. Columns not listed here are ignored.
COLUMN_MAP: dict[str, str] = {
    "ORDERNUMBER": "order_number",
    "PRODUCTCODE": "product_code",
    "ORDERLINENUMBER": "order_line_number",
    "QUANTITYORDERED": "quantity_ordered",
    "PRICEEACH": "price_each",
    "SALES": "sales",
    "TOTAL_SALES": "total_sales",
    "MSRP": "msrp",
    "ORDERDATE": "order_date",
    "STATUS": "status",
    "PRODUCTLINE": "product_line",
    "CUSTOMERNAME": "customer_name",
    "CITY": "city",
    "COUNTRY": "country",
    "TERRITORY": "territory",
    "DEALSIZE": "deal_size",
}
