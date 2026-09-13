import pytest
import app as app_module


@pytest.fixture()
def client():
    app_module.queue = app_module.JobQueue()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


def test_enqueue_claim_and_complete(client):
    response = client.post("/api/jobs", json={"task": "send-email"})
    assert response.status_code == 202
    job_id = response.get_json()["id"]

    claimed = client.post("/api/jobs/claim")
    assert claimed.status_code == 200
    assert claimed.get_json()["status"] == "processing"

    completed = client.post(
        f"/api/jobs/{job_id}/complete", json={"result": "sent"}
    )
    assert completed.status_code == 200
    assert completed.get_json()["status"] == "completed"


def test_failed_job(client):
    response = client.post("/api/jobs", json={"task": "resize-image"})
    job_id = response.get_json()["id"]
    client.post("/api/jobs/claim")

    failed = client.post(
        f"/api/jobs/{job_id}/fail", json={"error": "worker timeout"}
    )
    assert failed.status_code == 200
    assert failed.get_json()["status"] == "failed"


def test_empty_claim(client):
    assert client.post("/api/jobs/claim").status_code == 204


def test_invalid_enqueue(client):
    assert client.post("/api/jobs", json={}).status_code == 400


def test_missing_job(client):
    assert client.get("/api/jobs/not-found").status_code == 404


def test_stats(client):
    client.post("/api/jobs", json={"task": "a"})
    client.post("/api/jobs", json={"task": "b"})
    stats = client.get("/api/jobs/stats").get_json()
    assert stats["total"] == 2
    assert stats["queued"] == 2
