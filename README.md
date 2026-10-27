# Sales CSV Ingestion Pipeline

Upload a sales CSV, clean it with a Pandas ETL, store it in PostgreSQL, and explore it in a React dashboard.

**Stack:** FastAPI, Pandas, SQLAlchemy, PostgreSQL, React (Vite), Recharts, Docker Compose.

## Prerequisites

- Docker with Docker Compose
- `sales_data_sample.csv` from Kaggle: https://www.kaggle.com/datasets/kyanyoga/sample-sales-data

## Setup

```bash
docker compose up --build
```

- App: http://localhost:3000. Register an account, then upload the CSV.
- API docs (Swagger): http://localhost:8000/docs

## Testing

```bash
(cd backend && pip install -r requirements-dev.txt && pytest)
(cd frontend && npm install && npm test)
```

## API

All endpoints except register and login require `Authorization: Bearer <token>`.

| Endpoint | Description |
|---|---|
| `POST /api/register` | Create an account (`{email, password}`) |
| `POST /api/login` | Form fields `username` (email) and `password`; returns a JWT |
| `POST /api/upload` | Upload a CSV; returns the dataset ID and stats (row count, rows dropped, date range, total sales). With `?async=true`, processes in the background and returns 202 |
| `GET /api/datasets` | List the user's datasets with stats |
| `GET /api/datasets/{id}` | Paginated records and aggregates. Supports `page`, `page_size`, `sort_by`, `sort_dir`, `status`, `product_line`, `date_from`, `date_to` |
| `GET /api/datasets/{id}/status` | Processing status and progress |

## Assumptions

- **Required columns:** `ORDERNUMBER, PRODUCTCODE, QUANTITYORDERED, PRICEEACH, SALES, ORDERDATE, STATUS, PRODUCTLINE, COUNTRY`. Files missing any of them are rejected with 400.
- **Nulls:**
  - Rows missing a critical numeric field (`ORDERNUMBER`, `QUANTITYORDERED`, `PRICEEACH`, `SALES`) or `PRODUCTCODE` are **dropped**: they can't be deduplicated or counted in sales, and filling them would invent revenue.
  - `MSRP` nulls are **filled with the median**.
  - Empty `STATUS`/`PRODUCTLINE`/`COUNTRY` become `"Unknown"`.
- **Dates:** rows with an unparseable `ORDERDATE` are dropped.
- **Deduplication:** on `ORDERNUMBER + PRODUCTCODE`, keeping the first occurrence.
- **Derived column:** `TOTAL_SALES = QUANTITYORDERED × PRICEEACH`. The reported total sales uses the `SALES` column, because `PRICEEACH` is capped at 100 in this dataset.
- **Encoding:** the Kaggle file is latin-1 encoded; the parser falls back to latin-1 when UTF-8 fails.
- **Background processing:** uses FastAPI `BackgroundTasks`. A task queue (e.g. Celery) would suit production.
- **Schema:** tables are created on startup. After changing the schema, reset the database with `docker compose down -v`.
