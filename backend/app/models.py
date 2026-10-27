from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Monetary values: exact NUMERIC in the database, floats in Python (JSON-friendly).
Money = Numeric(14, 2, asdecimal=False)
JsonType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DatasetStatus:
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    datasets: Mapped[list["Dataset"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default=DatasetStatus.PROCESSING)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    rows_in: Mapped[int | None] = mapped_column(Integer)
    row_count: Mapped[int | None] = mapped_column(Integer)
    rows_dropped: Mapped[int | None] = mapped_column(Integer)
    drop_breakdown: Mapped[dict | None] = mapped_column(JsonType)
    date_min: Mapped[date | None] = mapped_column(Date)
    date_max: Mapped[date | None] = mapped_column(Date)
    total_sales: Mapped[float | None] = mapped_column(Money)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped[User] = relationship(back_populates="datasets")
    records: Mapped[list["Record"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", passive_deletes=True
    )


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (
        Index("ix_records_dataset_order_date", "dataset_id", "order_date"),
        Index("ix_records_dataset_status", "dataset_id", "status"),
        Index("ix_records_dataset_product_line", "dataset_id", "product_line"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))

    order_number: Mapped[int] = mapped_column(Integer)
    product_code: Mapped[str] = mapped_column(String(50))
    order_line_number: Mapped[int | None] = mapped_column(Integer)
    quantity_ordered: Mapped[int] = mapped_column(Integer)
    price_each: Mapped[float] = mapped_column(Money)
    sales: Mapped[float] = mapped_column(Money)
    total_sales: Mapped[float] = mapped_column(Money)
    msrp: Mapped[float | None] = mapped_column(Money)
    order_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50))
    product_line: Mapped[str] = mapped_column(String(100))
    customer_name: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    territory: Mapped[str | None] = mapped_column(String(50))
    deal_size: Mapped[str | None] = mapped_column(String(20))

    dataset: Mapped[Dataset] = relationship(back_populates="records")
