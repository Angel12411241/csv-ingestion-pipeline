"""Load step of the ETL: run the transform and persist records, tracking progress on the dataset row."""

import logging

import pandas as pd
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session, sessionmaker

from app.etl.pipeline import ETLError, to_records, transform
from app.models import Dataset, DatasetStatus, Record

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
# Progress is reported as: 0-10 upload/parse (done by the request), 10-30 transform, 30-100 load.
PROGRESS_TRANSFORMED = 30


def _set_progress(session: Session, dataset: Dataset, progress: int) -> None:
    dataset.progress = progress
    session.commit()


def process_dataset(dataset_id: int, raw_df: pd.DataFrame, session_factory: sessionmaker) -> None:
    """Transform `raw_df` and load it into `records` for the given dataset.

    Opens its own session so it can run as a background task after the request has finished.
    Records are committed in chunks so progress is visible to pollers; on failure, any partially
    loaded records are removed and the dataset is marked as failed.
    """
    with session_factory() as session:
        dataset = session.get(Dataset, dataset_id)
        if dataset is None:
            logger.warning("Dataset %s disappeared before processing", dataset_id)
            return
        try:
            clean_df, report = transform(raw_df)
            _set_progress(session, dataset, PROGRESS_TRANSFORMED)

            rows = to_records(clean_df)
            for start in range(0, len(rows), CHUNK_SIZE):
                chunk = [{**row, "dataset_id": dataset_id} for row in rows[start : start + CHUNK_SIZE]]
                session.execute(insert(Record), chunk)
                loaded = start + len(chunk)
                _set_progress(session, dataset, PROGRESS_TRANSFORMED + (100 - PROGRESS_TRANSFORMED) * loaded // len(rows))

            dataset.rows_in = report.rows_in
            dataset.row_count = report.rows_out
            dataset.rows_dropped = report.rows_dropped
            dataset.drop_breakdown = report.drop_breakdown
            dataset.date_min = report.date_min
            dataset.date_max = report.date_max
            dataset.total_sales = report.total_sales
            dataset.status = DatasetStatus.COMPLETED
            dataset.progress = 100
            session.commit()
        except Exception as exc:
            logger.exception("Processing dataset %s failed", dataset_id)
            session.rollback()
            session.execute(delete(Record).where(Record.dataset_id == dataset_id))
            dataset.status = DatasetStatus.FAILED
            dataset.error_message = str(exc) if isinstance(exc, ETLError) else "Unexpected error while processing the file."
            session.commit()
