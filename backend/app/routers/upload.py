from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import get_db, get_sessionmaker
from app.deps import get_current_user
from app.etl.pipeline import ETLError, extract, validate_columns
from app.models import Dataset, DatasetStatus, User
from app.schemas import DateRange, UploadResponse
from app.services.ingestion import process_dataset

router = APIRouter(tags=["upload"])

# Extract + validation happen inside the request, so the dataset starts at 10%.
PROGRESS_EXTRACTED = 10


def _read_upload(file: UploadFile) -> bytes:
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv files are accepted")
    limit = get_settings().max_upload_mb * 1024 * 1024
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {get_settings().max_upload_mb} MB limit",
        )
    return content


def _to_response(dataset: Dataset) -> UploadResponse:
    response = UploadResponse(dataset_id=dataset.id, filename=dataset.filename, status=dataset.status)
    if dataset.status == DatasetStatus.COMPLETED:
        response.row_count = dataset.row_count
        response.rows_dropped = dataset.rows_dropped
        response.drop_breakdown = dataset.drop_breakdown
        response.date_range = DateRange(start=dataset.date_min, end=dataset.date_max)
        response.total_sales = dataset.total_sales
    return response


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={202: {"description": "Accepted for background processing (async=true)"}},
)
def upload_csv(
    response: Response,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Sales CSV file"),
    run_async: bool = Query(False, alias="async", description="Process in the background and poll /status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_factory: sessionmaker = Depends(get_sessionmaker),
) -> UploadResponse:
    """Upload a sales CSV and run the ETL.

    The file is parsed and its columns validated synchronously, so invalid files are rejected with
    400 in both modes. By default the transform + load also run inside the request and the response
    contains the statistics (201). With `?async=true` they run in the background and the response is
    202; poll `GET /api/datasets/{id}/status` for progress.
    """
    content = _read_upload(file)
    try:
        raw_df = extract(content)
        validate_columns(raw_df)
    except ETLError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    dataset = Dataset(
        user_id=user.id,
        filename=file.filename,
        status=DatasetStatus.PROCESSING,
        progress=PROGRESS_EXTRACTED,
    )
    db.add(dataset)
    db.commit()

    if run_async:
        background_tasks.add_task(process_dataset, dataset.id, raw_df, session_factory)
        response.status_code = status.HTTP_202_ACCEPTED
        return _to_response(dataset)

    process_dataset(dataset.id, raw_df, session_factory)
    db.refresh(dataset)
    if dataset.status == DatasetStatus.FAILED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=dataset.error_message)
    return _to_response(dataset)
