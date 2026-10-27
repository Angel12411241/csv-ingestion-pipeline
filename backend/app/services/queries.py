"""Read side of the dashboard: filtered, sorted, paginated records and SQL aggregates."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Record

SORTABLE_COLUMNS = {
    "order_date": Record.order_date,
    "order_number": Record.order_number,
    "product_code": Record.product_code,
    "product_line": Record.product_line,
    "status": Record.status,
    "customer_name": Record.customer_name,
    "country": Record.country,
    "quantity_ordered": Record.quantity_ordered,
    "price_each": Record.price_each,
    "sales": Record.sales,
    "total_sales": Record.total_sales,
}


@dataclass
class RecordFilters:
    status: str | None = None
    product_line: str | None = None
    date_from: date | None = None
    date_to: date | None = None


def _filtered(stmt: Select, dataset_id: int, filters: RecordFilters) -> Select:
    stmt = stmt.where(Record.dataset_id == dataset_id)
    if filters.status:
        stmt = stmt.where(Record.status == filters.status)
    if filters.product_line:
        stmt = stmt.where(Record.product_line == filters.product_line)
    if filters.date_from:
        stmt = stmt.where(Record.order_date >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Record.order_date <= filters.date_to)
    return stmt


def get_records_page(
    db: Session,
    dataset_id: int,
    filters: RecordFilters,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> tuple[list[Record], int]:
    total = db.scalar(_filtered(select(func.count(Record.id)), dataset_id, filters)) or 0

    column = SORTABLE_COLUMNS[sort_by]
    order = column.desc() if sort_dir == "desc" else column.asc()
    stmt = (
        _filtered(select(Record), dataset_id, filters)
        .order_by(order, Record.id)  # id tiebreaker keeps pagination stable
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt)), total


def get_aggregates(db: Session, dataset_id: int, filters: RecordFilters) -> dict:
    total_sales, record_count = db.execute(
        _filtered(select(func.sum(Record.sales), func.count(Record.id)), dataset_id, filters)
    ).one()

    by_product_line = (
        select(Record.product_line, func.sum(Record.sales), func.count(Record.id))
        .group_by(Record.product_line)
        .order_by(func.sum(Record.sales).desc())
    )
    return {
        "total_sales": round(float(total_sales or 0), 2),
        "record_count": record_count,
        "sales_by_product_line": [
            {"label": label, "total_sales": round(float(total or 0), 2), "count": count}
            for label, total, count in db.execute(_filtered(by_product_line, dataset_id, filters))
        ],
    }


def get_filter_options(db: Session, dataset_id: int) -> dict:
    def distinct(column) -> list[str]:
        stmt = select(column).where(Record.dataset_id == dataset_id).distinct().order_by(column)
        return list(db.scalars(stmt))

    return {"statuses": distinct(Record.status), "product_lines": distinct(Record.product_line)}
