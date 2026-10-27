import math
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Dataset, DatasetStatus, User
from app.schemas import Aggregates, DatasetDetail, DatasetStatusOut, DatasetSummary, FilterOptions, RecordPage
from app.services.queries import (
    SORTABLE_COLUMNS,
    RecordFilters,
    get_aggregates,
    get_filter_options,
    get_records_page,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])

SortColumn = Literal[tuple(SORTABLE_COLUMNS)]  # type: ignore[valid-type]


def _get_owned_dataset(db: Session, dataset_id: int, user: User) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    # 404 (not 403) for other users' datasets so their existence is not leaked.
    if dataset is None or dataset.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("", response_model=list[DatasetSummary])
def list_datasets(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Dataset]:
    stmt = select(Dataset).where(Dataset.user_id == user.id).order_by(Dataset.created_at.desc(), Dataset.id.desc())
    return list(db.scalars(stmt))


@router.get("/{dataset_id}/status", response_model=DatasetStatusOut)
def get_dataset_status(
    dataset_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Dataset:
    return _get_owned_dataset(db, dataset_id, user)


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(
    dataset_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: SortColumn = Query("order_date"),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    status_filter: str | None = Query(None, alias="status"),
    product_line: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetDetail:
    """Paginated records plus aggregates for one dataset. Aggregates respect the active filters."""
    dataset = _get_owned_dataset(db, dataset_id, user)
    filters = RecordFilters(status=status_filter, product_line=product_line, date_from=date_from, date_to=date_to)

    if dataset.status != DatasetStatus.COMPLETED:
        # Records may be partially loaded (or rolled back); expose none until processing completes.
        items, total = [], 0
        aggregates = Aggregates(total_sales=0, record_count=0, sales_by_product_line=[])
        options = FilterOptions(statuses=[], product_lines=[])
    else:
        items, total = get_records_page(db, dataset.id, filters, sort_by, sort_dir, page, page_size)
        aggregates = Aggregates(**get_aggregates(db, dataset.id, filters))
        options = FilterOptions(**get_filter_options(db, dataset.id))

    return DatasetDetail(
        dataset=DatasetSummary.model_validate(dataset),
        records=RecordPage(
            items=items, total=total, page=page, page_size=page_size, pages=math.ceil(total / page_size)
        ),
        aggregates=aggregates,
        filter_options=options,
    )
