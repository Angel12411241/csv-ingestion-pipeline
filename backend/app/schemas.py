from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DateRange(BaseModel):
    start: date | None
    end: date | None


class DatasetSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    progress: int
    error_message: str | None
    rows_in: int | None
    row_count: int | None
    rows_dropped: int | None
    drop_breakdown: dict[str, int] | None
    date_min: date | None
    date_max: date | None
    total_sales: float | None
    created_at: datetime


class UploadResponse(BaseModel):
    """Returned by POST /api/upload. Stats are null while an async upload is still processing."""

    dataset_id: int
    filename: str
    status: str
    row_count: int | None = None
    rows_dropped: int | None = None
    drop_breakdown: dict[str, int] | None = None
    date_range: DateRange | None = None
    total_sales: float | None = None


class DatasetStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    progress: int
    error_message: str | None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: int
    product_code: str
    order_line_number: int | None
    quantity_ordered: int
    price_each: float
    sales: float
    total_sales: float
    msrp: float | None
    order_date: date
    status: str
    product_line: str
    customer_name: str | None
    city: str | None
    country: str
    territory: str | None
    deal_size: str | None


class RecordPage(BaseModel):
    items: list[RecordOut]
    total: int
    page: int
    page_size: int
    pages: int


class LabelValue(BaseModel):
    label: str
    total_sales: float
    count: int


class Aggregates(BaseModel):
    total_sales: float
    record_count: int
    sales_by_product_line: list[LabelValue]


class FilterOptions(BaseModel):
    statuses: list[str]
    product_lines: list[str]


class DatasetDetail(BaseModel):
    dataset: DatasetSummary
    records: RecordPage
    aggregates: Aggregates
    filter_options: FilterOptions
