# Distributed Job Queue

A small Flask-based job queue demonstrating producer/worker architecture and job lifecycle management.

## Features

- FIFO job enqueueing
- Worker-style job claiming
- Completed and failed states
- Thread-safe queue operations
- Job status lookup
- Queue statistics
- Health endpoint
- Pytest test suite

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/jobs` | Enqueue a job |
| POST | `/api/jobs/claim` | Claim next queued job |
| GET | `/api/jobs/<job_id>` | Get job status |
| POST | `/api/jobs/<job_id>/complete` | Complete a job |
| POST | `/api/jobs/<job_id>/fail` | Fail a job |
| GET | `/api/jobs/stats` | Queue statistics |

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Windows activation:

```powershell
.venv\Scripts\activate
```

Run tests:

```bash
pytest -q
```

## Example

```bash
curl -X POST http://localhost:5000/api/jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"task\":\"send-email\"}"
```

Claim the next job:

```bash
curl -X POST http://localhost:5000/api/jobs/claim
```

Complete it:

```bash
curl -X POST http://localhost:5000/api/jobs/JOB_ID/complete ^
  -H "Content-Type: application/json" ^
  -d "{\"result\":\"sent\"}"
```

## Architecture

```text
Producer
   |
   v
POST /api/jobs
   |
   v
+------------------+
|    Job Queue     |
|   FIFO + Lock    |
+------------------+
   |
   v
Worker -> claim
   |
   +--> complete
   |
   +--> fail
```

## Learning goals

This project introduces job lifecycle management, producer/worker separation, queue semantics, thread safety, and the foundation for replacing an in-memory queue with Redis, RabbitMQ, Kafka, or another durable broker.
