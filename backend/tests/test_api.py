import pytest

from tests.conftest import fixture_bytes


def test_upload_requires_authentication(client):
    files = {"file": ("sample_sales.csv", fixture_bytes("sample_sales.csv"), "text/csv")}
    assert client.post("/api/upload", files=files).status_code == 401


def test_upload_then_list_and_view_dataset(client, auth_headers, upload):
    response = upload("dirty_sales.csv")
    assert response.status_code == 201, response.text
    body = response.json()
    assert (body["row_count"], body["rows_dropped"]) == (3, 4)
    assert body["date_range"] == {"start": "2003-01-06", "end": "2003-03-02"}
    assert body["total_sales"] == 6101.0

    datasets = client.get("/api/datasets", headers=auth_headers).json()
    assert [d["id"] for d in datasets] == [body["dataset_id"]]

    detail = client.get(
        f"/api/datasets/{body['dataset_id']}",
        params={"page_size": 2, "sort_by": "sales", "sort_dir": "desc"},
        headers=auth_headers,
    ).json()
    records = detail["records"]
    assert (records["total"], records["pages"], len(records["items"])) == (3, 2, 2)
    assert [r["sales"] for r in records["items"]] == [5151.0, 600.0]
    assert detail["aggregates"]["total_sales"] == 6101.0


def test_detail_filters_apply_to_records_and_aggregates(client, auth_headers, upload):
    dataset_id = upload("sample_sales.csv").json()["dataset_id"]

    detail = client.get(
        f"/api/datasets/{dataset_id}",
        params={"status": "Shipped", "product_line": "Motorcycles", "date_from": "2003-03-01"},
        headers=auth_headers,
    ).json()
    assert [r["order_number"] for r in detail["records"]["items"]] == [10121]
    assert detail["aggregates"]["sales_by_product_line"] == [
        {"label": "Motorcycles", "total_sales": pytest.approx(2765.9), "count": 1}
    ]


def test_upload_rejects_missing_columns(upload):
    response = upload("missing_columns.csv")
    assert response.status_code == 400
    assert "SALES" in response.json()["detail"]


def test_async_upload_completes(client, auth_headers, upload):
    response = upload(**{"async": "true"})
    assert response.status_code == 202

    # TestClient runs background tasks before returning, so processing has finished by now.
    status = client.get(f"/api/datasets/{response.json()['dataset_id']}/status", headers=auth_headers).json()
    assert (status["status"], status["progress"]) == ("completed", 100)


def test_users_cannot_see_each_others_datasets(client, login, upload):
    dataset_id = upload().json()["dataset_id"]
    other = login("mallory@example.com")

    assert client.get("/api/datasets", headers=other).json() == []
    assert client.get(f"/api/datasets/{dataset_id}", headers=other).status_code == 404
